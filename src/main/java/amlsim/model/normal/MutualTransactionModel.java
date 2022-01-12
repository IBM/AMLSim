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

    public MutualTransactionModel(
        AccountGroup accountGroup,
        Random random
    ) {
        this.accountGroup = accountGroup;
        this.random = random;
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
    public void sendTransactions(long step, Account account) {
        if((step - this.startStep) % interval != 0)return;

        Account counterpart = account.getPrevOrig();
        if(counterpart == null){
            List<Account> origs = account.getOrigList();
            if(origs.isEmpty()) {
                return;
            }else{
                counterpart = origs.get(0);
            }
        }

        TargetedTransactionAmount transactionAmount = new TargetedTransactionAmount(account.getBalance(), random);

        if(!account.getBeneList().contains(counterpart)) {
            account.addBeneAcct(counterpart);    // Add a new destination
        }

        makeTransaction(step, transactionAmount.doubleValue(), account, counterpart);
    }
}
