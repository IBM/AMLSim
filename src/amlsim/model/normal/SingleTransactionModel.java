package amlsim.model.normal;

import amlsim.AMLSim;
import amlsim.Account;
import amlsim.model.AbstractTransactionModel;

import java.util.List;
import java.util.Random;

/**
 * Send money only for once to one of the neighboring accounts
 */
public class SingleTransactionModel extends AbstractTransactionModel {

    private static Random rand = new Random();
    
    /**
     * Simulation step when this transaction is done
     */
    private long txStep = -1;
    
    public String getType(){
        return "Single";
    }

    public void setParameters(int interval, float balance, long start, long end){
        super.setParameters(interval, balance, start, end);
        if(this.startStep < 0){
            this.startStep = 0;
        }
        if(this.endStep < 0){
            this.endStep = AMLSim.getNumOfSteps();
        }
        // The transaction step is determined randomly within the given range
        this.txStep = this.startStep + rand.nextInt((int)(endStep - startStep + 1));
    }
    
    public void sendTransaction(long step){
        List<Account> beneList = this.account.getBeneList();
        int numBene = beneList.size();
        if(step != this.txStep || numBene == 0){
            return;
        }

        float amount = getTransactionAmount();
        int index = rand.nextInt(numBene);
        Account dest = beneList.get(index);
        this.sendTransaction(step, amount, dest);
    }
}
