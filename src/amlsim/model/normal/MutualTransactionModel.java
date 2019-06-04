package amlsim.model.normal;

import amlsim.*;
import amlsim.model.AbstractTransactionModel;

import java.util.List;

/**
 * Return money to one of the previous senders
 */
public class MutualTransactionModel extends AbstractTransactionModel {

    private static final int INTERVAL = 10;

    @Override
    public String getType() {
        return "Mutual";
    }

    @Override
    public void sendTransaction(long step) {
        if((step - this.account.getStartStep()) % INTERVAL == 0){
            return;
        }

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
