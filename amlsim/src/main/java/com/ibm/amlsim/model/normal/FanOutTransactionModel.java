package com.ibm.amlsim.model.normal;

import com.ibm.amlsim.*;
import com.ibm.amlsim.model.AbstractTransactionModel;

import static java.lang.Math.min;
import java.util.*;

/**
 * Send money from single source to multiple destinations (fan-out)
 */
public class FanOutTransactionModel extends AbstractTransactionModel {

    private static final int INTERVAL = 10; // TODO: Enable users to specify this value

    @Override
    public String getType() {
        return "FanOut";
    }

    private boolean isValidStep(long step){
        return (step - this.account.getStartStep() + generateDiff()) % INTERVAL == 0;
    }

    @Override
    public void sendTransaction(long step) {
        List<Account> dests = this.account.getDests();  // Destination accounts
        int numDests = dests.size();
        if(numDests == 0){  // No destination accounts
            return;
        }
        if(!isValidStep(step)){
            return;
        }

        float amount = this.balance / numDests;  // Each amount is same TODO: make it flexible
        for(Account dest : dests) {
            this.sendTransaction(step, amount, dest);
        }
    }
}
