package amlsim.model.normal;

import amlsim.Account;
import amlsim.AMLSim;
import amlsim.model.AbstractTransactionModel;


/**
 * Send money to neighbors periodically
 */
public class PeriodicalTransactionModel extends AbstractTransactionModel {

    private int index = 0;
    private final int PERIOD = 10;  // TODO: accept user-defined periods from configurations

    @Override
    public String getType() {
        return "Periodical";
    }

    private boolean isValidStep(long step){
        return (step - account.getStartStep() + generateDiff()) % PERIOD == 0;
    }

    @Override
    public void sendTransaction(long step) {
        if(!isValidStep(step) || this.account.getDests().isEmpty()){
            return;
        }
        int numDests = this.account.getDests().size();
        if(index >= numDests)return;

        int totalRemit = (int)AMLSim.getNumOfSteps() / PERIOD; // Total number of remittances
        int eachRemit = (numDests < totalRemit) ? 1 : numDests / totalRemit;

        for(int i=0; i<eachRemit; i++) {
            float amount = this.balance;
            Account dest = this.account.getDests().get(index);
            this.sendTransaction(step, amount, dest);
            index++;
            if(index >= numDests) break;
        }
        index = 0;
    }

}
