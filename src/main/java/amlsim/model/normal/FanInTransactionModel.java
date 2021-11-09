package amlsim.model.normal;

import amlsim.*;
import amlsim.model.AbstractTransactionModel;

import java.util.*;

/**
 * Receive money from one of the senders (fan-in)
 */
public class FanInTransactionModel extends AbstractTransactionModel {

    private int index = 0;

    private Random random;
    private Account account;
    private TargetedTransactionAmount transactionAmount;

    public FanInTransactionModel(
        Account account,
        Random random
    ) {
        this.random = random;
        this.account = account;
    }

    public void setParameters(int interval, long start, long end){
        super.setParameters(interval, start, end);
        if(this.startStep < 0){  // decentralize the first transaction step
            this.startStep = generateStartStep(interval);
        }
    }


    @Override
    public String getModelName() {
        return "FanIn";
    }

    private boolean isValidStep(long step){
        return (step - startStep) % interval == 0;
    }

    @Override
    public void makeTransaction(long step) {
        List<Account> beneList = this.account.getBeneList();  // Destination accounts
        int numOrigs = beneList.size();
        if (!isValidStep(step) || numOrigs == 0) {
            return;
        }
        if (index >= numOrigs) {
            index = 0;
        }

        this.transactionAmount = new TargetedTransactionAmount(this.account.getBalance(), this.random);
        double amount = this.transactionAmount.doubleValue();
        
        Account bene = beneList.get(index);

        makeTransaction(step, amount, bene);
        index++;
    }
}
