package amlsim.model.normal;

import amlsim.*;
import amlsim.model.AbstractTransactionModel;

import java.util.List;
import java.util.Random;

/**
 * Return money to one of the previous senders
 */
public class MutualTransactionModel extends AbstractTransactionModel {

    private Random random;
    private Account account;

    public MutualTransactionModel(
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
        return "Mutual";
    }

    @Override
    public void makeTransaction(long step) {
        if((step - this.startStep) % interval != 0)return;

        Account counterpart = this.account.getPrevOrig();
        if(counterpart == null){
            List<Account> origs = this.account.getOrigList();
            if(origs.isEmpty()) {
                return;
            }else{
                counterpart = origs.get(0);
            }
        }

        TargetedTransactionAmount transactionAmount = new TargetedTransactionAmount(this.account.getBalance(), random);

        if(!this.account.getBeneList().contains(counterpart)) {
            this.account.addBeneAcct(counterpart);    // Add a new destination
        }

        makeTransaction(step, transactionAmount.doubleValue(), counterpart);
    }

}
