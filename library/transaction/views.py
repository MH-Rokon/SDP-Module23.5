# transaction/views.py

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.http import HttpResponse
from django.views.generic import CreateView, ListView
from transaction.constants import DEPOSIT, WITHDRAWAL, LOAN, LOAN_PAID, SENDMONEY, RECEIVEMONEY
from datetime import datetime
from django.db.models import Sum
from transaction.forms import DepositForm, WithdrawForm, LoanRequestForm, MoneyTransferForm
from transaction.models import Transaction
from accounts.models import UserBookAccount
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string

def send_transaction_email(user, amount, subject, template):
    message = render_to_string(template, {
        'user' : user,
        'amount' : amount,
    })
    send_email = EmailMultiAlternatives(subject, '', to=[user.email])
    send_email.attach_alternative(message, "text/html")
    send_email.send()

class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'transaction/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account': self.request.user.account
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': self.title
        })
        return context
    
class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = 'Deposit'

    def get_initial(self):
        initial = {'transaction_type': DEPOSIT}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account

        account.balance += amount 
        account.save(update_fields=['balance'])

        messages.success(
            self.request,
            f'{"{:,.2f}".format(float(amount))}$ was deposited to your account successfully'
        )
        send_transaction_email(self.request.user, amount, "Deposit Message", "transaction/deposit_email.html")

        return super().form_valid(form)

class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money'

    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')

        self.request.user.account.balance -= amount
        self.request.user.account.save(update_fields=['balance'])

        messages.success(
            self.request,
            f'Successfully withdrawn {"{:,.2f}".format(float(amount))}$ from your account'
        )
        send_transaction_email(self.request.user, amount, "Withdrawal Message", "transaction/withdraw_email.html")

        return super().form_valid(form)

class LoanRequestView(TransactionCreateMixin):
    form_class = LoanRequestForm
    title = 'Request For Loan'

    def get_initial(self):
        initial = {'transaction_type': LOAN}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        current_loan_count = Transaction.objects.filter(
            account=self.request.user.account, transaction_type=LOAN, loan_approve=True
        ).count()
        if current_loan_count >= 3:
            return HttpResponse("You have crossed the loan limits")
        messages.success(
            self.request,
            f'Loan request for {"{:,.2f}".format(float(amount))}$ submitted successfully'
        )

        return super().form_valid(form)

class TransactionReportView(LoginRequiredMixin, ListView):
    template_name = 'transaction/transaction_report.html'
    model = Transaction
    balance = 0 
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(
            account=self.request.user.account
        )
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')
        
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            queryset = queryset.filter(timestamp__date__gte=start_date, timestamp__date__lte=end_date)
            self.balance = Transaction.objects.filter(
                timestamp__date__gte=start_date, timestamp__date__lte=end_date
            ).aggregate(Sum('amount'))['amount__sum']
        else:
            self.balance = self.request.user.account.balance
       
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account': self.request.user.account
        })
        return context

class PayLoanView(LoginRequiredMixin, View):
    def get(self, request, loan_id):
        loan = get_object_or_404(Transaction, id=loan_id)
        if loan.loan_approve:
            user_account = loan.account
            if loan.amount < user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transaction = user_account.balance
                user_account.save()
                loan.loan_approved = True
                loan.transaction_type = LOAN_PAID
                loan.save()
                return redirect('transactions:loan_list')
            else:
                messages.error(
                    self.request,
                    f'Loan amount is greater than available balance'
                )
        return redirect('loan_list')

class LoanListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'transaction/loan_request.html'
    context_object_name = 'loans'
    
    def get_queryset(self):
        user_account = self.request.user.account
        queryset = Transaction.objects.filter(account=user_account, transaction_type=LOAN)
        return queryset

class MoneyTransferView(LoginRequiredMixin, View):
    template_name = 'transaction/transfer_money.html'

    def get(self, request):
        form = MoneyTransferForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = MoneyTransferForm(request.POST)

        if form.is_valid():
            amount = form.cleaned_data['amount']
            recipient_account_number = form.cleaned_data['recipient_account_number']

            sender_account = request.user.account
            try:
                recipient_account = UserBookAccount.objects.get(account_no=recipient_account_number)
            except UserBookAccount.DoesNotExist:
                recipient_account = None

            if recipient_account:
                if sender_account.balance >= amount:
                    sender_account.balance -= amount
                    sender_account.save()

                    Transaction.objects.create(
                        account=sender_account,
                        amount=-amount,
                        transaction_type=SENDMONEY,
                        balance_after_transaction=sender_account.balance,
                    )

                    recipient_account.balance += amount
                    recipient_account.save()

                    Transaction.objects.create(
                        account=recipient_account,
                        amount=amount,
                        transaction_type=RECEIVEMONEY,
                        balance_after_transaction=recipient_account.balance,
                    )

                    messages.success(request, f'Successfully transferred {"{:,.2f}".format(float(amount))}$ to account {recipient_account_number}')
                else:
                    messages.error(request, 'Insufficient funds for the money transfer')
            else:
                messages.error(request, 'Recipient account not found')
        else:
            messages.error(request, 'Invalid form submission')

        return redirect('transaction_report')
