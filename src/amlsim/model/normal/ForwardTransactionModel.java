package amlsim.model.normal;

import amlsim.AMLSim;
import amlsim.Account;
import amlsim.model.AbstractTransactionModel;

import java.util.*;

/**
 * Send money received from an account to another account in a similar way
 */
public class ForwardTransactionModel extends AbstractTransactionModel {
    private int index = 0;

    @Override
    public String getType() {
        return "Forward";
    }

    @Override
    public void sendTransaction(long step) {

        float amount = getTransactionAmount();  // this.balance;
        List<Account> dests = this.account.getDests();
        int numDests = dests.size();
        if(numDests == 0){
            return;
        }
        if(step % interval != this.account.getStartStep() % interval){
            return;
        }

        if(index < numDests){
            Account dest = dests.get(index);
            this.sendTransaction(step, amount, dest);
            index++;
        }
//        for(Account dest : dests){
//            this.sendTransaction(step, amount, dest);
//        }
    }
}
