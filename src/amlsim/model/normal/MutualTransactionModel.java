package amlsim.model.normal;

import amlsim.*;
import amlsim.model.AbstractTransactionModel;

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
        float amount = this.receivedAmount;
        if(!this.account.getDests().contains(counterpart)) {
            this.account.addDest(counterpart);    // Add a new destination
        }

        sendTransaction(step, amount, counterpart);
    }

}
