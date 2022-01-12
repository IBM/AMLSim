package amlsim.model.cash;

import amlsim.AMLSim;
import amlsim.Account;
import amlsim.model.AbstractTransactionModel;

import java.util.Random;

/**
 * Cash transaction model (between an account and a deposit account)
 * There are two subclasses: CashInModel (deposit) and CashOutModel (withdrawal)
 */
public abstract class CashModel extends AbstractTransactionModel {

    protected static Random rand = AMLSim.getRandom();

    // needed for cash accounts temporarily
    protected Account account;

    protected double[] randValues;  // Random values to generate transaction amounts
    protected static final int randSize = 10;  // Number of random values to be stored

    public void setAccount(Account account) {
        this.account = account;
    }

    public CashModel(){
        randValues = new double[randSize];
        for(int i = 0; i< randSize; i++){
            randValues[i] = rand.nextGaussian();  // from -1.0 to 1.0
        }
    }

    // to satisfy interface
    public void sendTransactions(long step, Account acct) {

    }

    // Abstract methods from TransactionModel
    public abstract String getModelName();  // Get transaction type description
    public abstract void makeTransaction(long step);  // Create and add transactions
}
