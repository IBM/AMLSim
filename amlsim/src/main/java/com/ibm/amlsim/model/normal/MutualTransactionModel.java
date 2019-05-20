package com.ibm.amlsim.model.normal;

import com.ibm.amlsim.*;
import com.ibm.amlsim.model.AbstractTransactionModel;

import java.util.List;

/**
 * Return money to one of the previous senders
 */
public class MutualTransactionModel extends AbstractTransactionModel {


    @Override
    public String getType() {
        return "Mutual";
    }

    @Override
    public void sendTransaction(long step) {
        Account counterpart = this.account.getPrevOrig();
        if(counterpart == null){
            List<Account> origs = this.account.getOrigs();
            if(origs.isEmpty()) {
                return;
            }else{
                counterpart = origs.get(0);
            }
        }
        float amount = this.balance;
        if(!this.account.getDests().contains(counterpart)) {
            this.account.addDest(counterpart);    // Add a new destination
        }

        sendTransaction(step, amount, counterpart);
    }

}
