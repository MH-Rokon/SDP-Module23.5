from django.urls import path
from .views import DepositMoneyView, WithdrawMoneyView, TransactionReportView,LoanRequestView,LoanListView,PayLoanView,MoneyTransferView

from . import views
# app_name = 'transactions'
urlpatterns = [
    path("deposit/", DepositMoneyView.as_view(), name="deposit_money"),
    path("report/", TransactionReportView.as_view(), name="transaction_report"),
    path("withdraw/", WithdrawMoneyView.as_view(), name="withdraw_money"),
    path("loan_request/", LoanRequestView.as_view(), name="loan_request"),
    path("loans/", LoanListView.as_view(), name="loan_list"),
    path("loans/<int:loan_id>/", PayLoanView.as_view(), name="pay"),
    path('money-transfer/', MoneyTransferView.as_view(), name='money_transfer'),
]

#   path("withdraw_books/", WithdrawBookView.as_view(), name="withdraw_books"),
#   path("books/", bookView.as_view(), name="books"),