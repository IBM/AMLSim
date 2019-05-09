package amlsim.model.normal;

import amlsim.*;
import amlsim.model.AbstractTransactionModel;
import java.util.*;

/**
 * Receive money from one of the senders (fan-in)
 */
public class FanInTransactionModel extends AbstractTransactionModel {

    private int index = 0;

    @Override
    public String getType() {
        return "FanIn";
    }

    private boolean isValidStep(long step){
        return (step - this.account.getStartStep() + generateDiff()) % interval == 0;
    }

    @Override
    public void sendTransaction(long step) {
        List<Account> origs = this.account.getOrigs();  // Sender accounts
        int numOrigs = origs.size();
        if(numOrigs == 0 || index >= numOrigs){
            return;
        }

        if(!isValidStep(step)){
            return;
        }

//        int newIndex = index % numDests;
//        Account dest = dests.get(newIndex);  // Select one of the destinations
//        float amount = 0;
//        for (Account orig : origs) {
//            amount += orig.getBalance();
//        }
//        amount /= numDests;
//        sendTransaction(step, amount, dest);
        Account orig = origs.get(index);
        float amount = orig.getModel().getTransactionAmount();
        sendTransaction(step, amount, orig, this.account);
        index++;
    }
}
