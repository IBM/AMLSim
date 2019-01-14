package amlsim.model.normal;

import amlsim.Account;
import amlsim.model.AbstractTransactionModel;

import java.util.*;

/**
 * Send money received from an account to another account in a similar way
 */
public class ForwardTransactionModel extends AbstractTransactionModel {
    private int index = 0;
    private static final int INTERVAL = 10;

    @Override
    public String getType() {
        return "Forward";
    }

    @Override
    public void sendTransaction(long step) {

        float amount = this.balance;
        List<Account> dests = this.account.getDests();
        int numDests = dests.size();
        if(numDests == 0){
            return;
        }
        if(step % INTERVAL != this.account.getStartStep() % INTERVAL){
            return;
        }

        for(Account dest : dests){
            this.sendTransaction(step, amount, dest);
        }
    }
}
