package amlsim.obsolete;

import amlsim.Account;
import amlsim.AMLSim;
import amlsim.model.AbstractTransactionModel;

import java.util.List;

/**
 * Send small amount of money with high frequency
 * @deprecated Use "FanOutTransactionModel" instead
 */
public class FineGrainedTransactionModel extends AbstractTransactionModel {
    private int index = 0;
    private final int FREQUENCY = 1;

    @Override
    public String getType() {
        return "FineGrained";
    }

    @Override
    public void sendTransaction(long step) {

        List<Account> dests = this.account.getDests();
        if(dests.isEmpty())return;

        int numDests = dests.size();
        int eachRemit = (int)AMLSim.getNumOfSteps() / numDests;

        float amount = this.balance / FREQUENCY;
        for(int i=0; i<eachRemit; i++) {
            int newIndex = index + i;
            if(newIndex >= numDests * FREQUENCY)break;

            Account dest = dests.get(newIndex % numDests);
            this.sendTransaction(step, amount, dest);
        }
        index += eachRemit;
    }

}

