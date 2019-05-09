package amlsim.model.normal;

import amlsim.Account;
import amlsim.AMLSim;
import amlsim.model.AbstractTransactionModel;


/**
 * Send money to neighbors periodically
 */
public class PeriodicalTransactionModel extends AbstractTransactionModel {

    private int index = 0;

    @Override
    public String getType() {
        return "Periodical";
    }

    private boolean isValidStep(long step){
        return (step - account.getStartStep() + generateDiff()) % interval == 0;
    }

    @Override
    public void sendTransaction(long step) {
        if(!isValidStep(step) || this.account.getDests().isEmpty()){
            return;
        }
        int numDests = this.account.getDests().size();
        if(index >= numDests)return;

        int totalCount = getNumberOfTransactions();  // Total number of transactions
        int eachCount = (numDests < totalCount) ? 1 : numDests / totalCount;

        for(int i=0; i<eachCount; i++) {
            float amount = getTransactionAmount();  // this.balance;
            Account dest = this.account.getDests().get(index);
            this.sendTransaction(step, amount, dest);
            index++;
            if(index >= numDests) break;
        }
        index = 0;
    }
}
