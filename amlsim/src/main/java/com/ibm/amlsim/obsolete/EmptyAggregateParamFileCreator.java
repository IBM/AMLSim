package com.ibm.amlsim.obsolete;

import paysim.AggregateParamFileCreator;
import paysim.AggregateTransactionRecord;
import paysim.Transaction;

import java.util.ArrayList;
import java.util.Collections;

/**
 * @deprecated This class is obsolete
 * Output empty aggregated data because it is memory overhead in AMLSim
 */
public class EmptyAggregateParamFileCreator extends AggregateParamFileCreator {

    public ArrayList<AggregateTransactionRecord> generateAggregateParamFile(ArrayList<Transaction> transactionList) {
        // Return empty list
        return new ArrayList<AggregateTransactionRecord>();
//        ArrayList<AggregateTransactionRecord> aggrTransRecord = new ArrayList<>();
//        return aggrTransRecord;
    }

}
