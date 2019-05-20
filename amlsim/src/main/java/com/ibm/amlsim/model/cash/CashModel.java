package com.ibm.amlsim.model.cash;

import com.ibm.amlsim.model.AbstractTransactionModel;

import java.util.Random;

/**
 * Transaction model between an account and the deposit account
 * There are two subclasses: CashInModel (deposit) and CashOutModel (withdrawal)
 */
public abstract class CashModel extends AbstractTransactionModel {

    protected static Random rand = new Random();

    protected double[] randValues;  // Random values to generate transaction amounts
    protected static final int rsize = 10;  // Number of random values to be stored

    public CashModel(){
        randValues = new double[rsize];
        for(int i=0; i<rsize; i++){
            randValues[i] = rand.nextGaussian();  // from -1.0 to 1.0
        }
    }

    // Abstract methods from TransactionModel
    public abstract String getType();  // Get transaction type description
    public abstract void sendTransaction(long step);  // Create and add transactions
}
