package amlsim.model.normal;

import amlsim.*;
import amlsim.model.AbstractTransactionModel;

import static java.lang.Math.min;
import java.util.*;

/**
 * Send money from single source to multiple destinations (fan-out)
 */
public class FanOutTransactionModel extends AbstractTransactionModel {

    private static final int INTERVAL = 10;

    @Override
    public String getType() {
        return "FanOut";
    }

    @Override
    public void sendTransaction(long step) {
        List<Account> dests = this.account.getDests();
        int numDests = dests.size();
        if(numDests == 0){
            return;
        }
        if(step % INTERVAL != this.account.getStartStep() % INTERVAL){
            return;
        }

        float amount = this.receivedAmount / numDests;
        for(Account dest : dests) {
            this.sendTransaction(step, amount, dest);
        }
    }
}
