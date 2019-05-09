package amlsim.model.normal;

import amlsim.*;
import amlsim.model.AbstractTransactionModel;
import java.util.*;

/**
 * Send money from single source to multiple destinations (fan-out)
 */
public class FanOutTransactionModel extends AbstractTransactionModel {

    private int index = 0;

    @Override
    public String getType() {
        return "FanOut";
    }

    private boolean isValidStep(long step){
        return (step - this.account.getStartStep() + generateDiff()) % interval == 0;
    }

    @Override
    public void sendTransaction(long step) {
        List<Account> dests = this.account.getDests();  // Destination accounts
        int numDests = dests.size();
        if(numDests == 0 || index >= numDests){  // No more destination accounts
            return;
        }
        if(!isValidStep(step)){
            return;
        }

        float amount = getTransactionAmount();
        Account dest = dests.get(index);
        this.sendTransaction(step, amount, dest);
        index++;
    }
}
