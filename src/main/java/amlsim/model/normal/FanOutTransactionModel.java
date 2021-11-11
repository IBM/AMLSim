package amlsim.model.normal;

import amlsim.*;
import amlsim.model.AbstractTransactionModel;

import java.util.*;

/**
 * Distribute money to multiple neighboring accounts (fan-out)
 */
public class FanOutTransactionModel extends AbstractTransactionModel {

    private int index = 0;
    
    private Random random;
    private Account account;
    private TargetedTransactionAmount transactionAmount;

    public FanOutTransactionModel(
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
        return "FanOut";
    }

    private boolean isValidStep(long step){
        return (step - startStep) % interval == 0;
    }

    @Override
    public void makeTransaction(long step) {
        List<Account> beneList = this.account.getBeneList();  // Destination accounts
        int numBene = beneList.size();
        if (!isValidStep(step) || numBene == 0) { // No more destination accounts
            return;
        }
        if (index >= numBene) {
            index = 0;
        }

        this.transactionAmount = new TargetedTransactionAmount(this.account.getBalance(), random);
        double amount = this.transactionAmount.doubleValue();

        Account bene = beneList.get(index);

        if (amount > 0) {
            this.makeTransaction(step, amount, bene);
        }
        index++;
    }
}
