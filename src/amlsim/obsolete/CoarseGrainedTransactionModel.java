package amlsim.obsolete;

import amlsim.*;
import amlsim.model.AbstractTransactionModel;

import static java.lang.Math.max;
import static java.lang.Math.min;

/**
 * Send large amount of money with less frequency
 * @deprecated Use "FanInTransactionModel" instead
 */
public class CoarseGrainedTransactionModel extends AbstractTransactionModel {

    @Override
    public String getType() {
        return "CoarseGrained";
    }

    @Override
    public void sendTransaction(long step) {
        if(step < this.startStep || this.endStep < step || this.account.getDests().isEmpty()){
            return;
        }
        float amount = this.balance;

        int numDests = this.account.getDests().size();
        int numPerStep = max(numDests / ((int)this.endStep - (int)this.startStep + 1), 1);
        int start = numPerStep * (int)(step - this.startStep);
        int end = min(numPerStep * (int)(step - this.startStep + 1), numDests);

//        List<AMLTransaction> txs = new ArrayList<>();

        for(int i=start; i<end; i++) {
            Account dest = this.account.getDests().get(i);
            this.sendTransaction(step, amount, dest);
//            txs.add(tx);
        }
//        return txs;
    }

//    @Override
//    public void sent() {
//
//    }
}

