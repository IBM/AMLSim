package amlsim.model.cash;

import amlsim.AMLSim;
import amlsim.model.AbstractTransactionModel;

import java.util.Random;

/**
 * Cash transaction model (between an account and a deposit account)
 * There are two subclasses: CashInModel (deposit) and CashOutModel (withdrawal)
 */
public abstract class CashModel extends AbstractTransactionModel {

//    protected static Random rand = new Random();
    protected static Random rand = AMLSim.getRandom();

    protected double[] randValues;  // Random values to generate transaction amounts
    protected static final int randSize = 10;  // Number of random values to be stored

    public CashModel(){
        randValues = new double[randSize];
        for(int i = 0; i< randSize; i++){
            randValues[i] = rand.nextGaussian();  // from -1.0 to 1.0
        }
    }

    // Abstract methods from TransactionModel
    public abstract String getModelName();  // Get transaction type description
    public abstract void makeTransaction(long step);  // Create and add transactions
}
