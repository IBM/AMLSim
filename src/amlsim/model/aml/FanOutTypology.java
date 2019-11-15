//
// Note: No specific bank models are used for this AML typology model class.
//

package amlsim.model.aml;

import amlsim.Account;

import java.util.*;

/**
 * The main account distributes money to multiple members
 */
public class FanOutTypology extends AMLTypology {

    // Originator and beneficiary accounts
    private Account orig;
    private List<Account> beneList = new ArrayList<>();

    private long[] steps;

    FanOutTypology(float minAmount, float maxAmount, int minStep, int maxStep){
        super(minAmount, maxAmount, minStep, maxStep);
    }

    public int getNumTransactions(){
        return alert.getMembers().size() - 1;
    }

    public void setParameters(int scheduleID){
        // Set members
        List<Account> members = alert.getMembers();
        Account mainAccount = alert.getMainAccount();
        orig = mainAccount != null ? mainAccount : members.get(0);
        for(Account bene : members){
            if(orig != bene) beneList.add(bene);
        }

        // Set schedule
        int numBenes = beneList.size();
        int totalStep = (int)(endStep - startStep + 1);
        int defaultInterval = Math.max(totalStep / numBenes, 1);
        this.startStep = generateStartStep(defaultInterval);  //  decentralize the first transaction step

        steps = new long[numBenes];
        if(scheduleID == SIMULTANEOUS){
            long step = getRandomStep();
            Arrays.fill(steps, step);
        }else if(scheduleID == FIXED_INTERVAL){
            int range = (int)(endStep - startStep + 1);
            if(numBenes < range){
                interval = range / numBenes;
                for(int i=0; i<numBenes; i++){
                    steps[i] = startStep + interval*i;
                }
            }else{
                long batch = numBenes / range;
                for(int i=0; i<numBenes; i++){
                    steps[i] = startStep + i/batch;
                }
            }
        }else if(scheduleID == RANDOM_INTERVAL || scheduleID == UNORDERED){
            for(int i=0; i<numBenes; i++){
                steps[i] = getRandomStep();
            }
        }
    }

    @Override
    public String getType() {
        return "FanOutTypology";
    }

    @Override
    public void sendTransactions(long step, Account acct) {
        if(!orig.getID().equals(acct.getID())){
            return;
        }
        long alertID = alert.getAlertID();
        boolean isSAR = alert.isSAR();
        float amount = getRandomAmount();

        for(int i = 0; i< beneList.size(); i++){
            if(steps[i] == step){
                Account bene = beneList.get(i);
                sendTransaction(step, amount, orig, bene, isSAR, alertID);
            }
        }
    }
}
