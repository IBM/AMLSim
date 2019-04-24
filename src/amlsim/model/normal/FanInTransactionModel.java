package amlsim.model.normal;

import amlsim.*;
import amlsim.model.AbstractTransactionModel;

import java.util.*;

/**
 * Send money (from multiple senders) to one of the destinations (fan-in)
 */
public class FanInTransactionModel extends AbstractTransactionModel {

    private final int INTERVAL = 10; // TODO: Enable users to specify this value
    private int index = 0;

    @Override
    public String getType() {
        return "FanIn";
    }

    private boolean isValidStep(long step){
        return (step - this.account.getStartStep() + generateDiff()) % INTERVAL == 0;
    }

    @Override
    public void sendTransaction(long step) {
        List<Account> origs = this.account.getOrigs();  // Sender accounts
        List<Account> dests = this.account.getDests();  // Receiver accounts
        int numDests = dests.size();
        if(numDests == 0){
            return;
        }

        if(!isValidStep(step)){
            return;
        }

        int newIndex = index % numDests;
        Account dest = dests.get(newIndex);  // Select one of the destinations
        float amount = 0;
        for (Account orig : origs) {
            amount += orig.getBalance();
        }
        amount /= numDests;
        sendTransaction(step, amount, dest);
        index++;
    }
}
