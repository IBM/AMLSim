package amlsim.model.normal;

import java.util.Random;


import amlsim.Account;
import amlsim.TargetedTransactionAmount;
import amlsim.model.AbstractTransactionModel;


/**
 * Send money to neighbors periodically
 */
public class PeriodicalTransactionModel extends AbstractTransactionModel {

    private int index = 0;

    private Random random;
    private Account account;

    public PeriodicalTransactionModel(
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
        return "Periodical";
    }

    private boolean isValidStep(long step){
        return (step - startStep) % interval == 0;
    }

    @Override
    public void makeTransaction(long step) {
        if(!isValidStep(step) || this.account.getBeneList().isEmpty()){
            return;
        }
        int numDests = this.account.getBeneList().size();
        if(index >= numDests){
            index = 0;
        }

        int totalCount = getNumberOfTransactions();  // Total number of transactions
        int eachCount = (numDests < totalCount) ? 1 : numDests / totalCount;

        TargetedTransactionAmount transactionAmount = new TargetedTransactionAmount(this.account.getBalance() / eachCount, random);

        for (int i = 0; i < eachCount; i++) {
            Account dest = this.account.getBeneList().get(index);
            this.makeTransaction(step, transactionAmount.doubleValue(), dest);
            index++;
            if (index >= numDests)
                break;
        }
        index = 0;
    }
}
