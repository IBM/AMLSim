//
// Note: No specific bank models are used for this AML typology model class.
//

package amlsim.model.aml;

import amlsim.Account;

import java.util.*;

/**
 * Multiple accounts send money to the subject account
 */
public class FanInTypology extends AMLTypology {

    // Originators and the main beneficiary
    private Account bene;  // The destination (beneficiary) account
    private List<Account> origList = new ArrayList<>();  // The origin (originator) accounts

    private long[] steps;
    private static final int SIMULTANEOUS = 1;
    private static final int FIXED_INTERVAL = 2;
    private static final int RANDOM_RANGE = 3;

    FanInTypology(float minAmount, float maxAmount, int start, int end){
        super(minAmount, maxAmount, start, end);
    }

    public void setParameters(int schedulingID){

        // Set members
        List<Account> members = alert.getMembers();
        bene = alert.isSAR() ? alert.getMainAccount() : members.get(0);  // The subject account is the receiver
        for(Account orig : members){  // The rest of accounts are originators
            if(orig != bene) origList.add(orig);
        }

        // Set transaction schedule
        int numOrigs = origList.size();
        int totalStep = (int)(endStep - startStep + 1);
        int defaultInterval = totalStep / numOrigs;
        this.startStep = generateStartStep(defaultInterval);  //  decentralize the first transaction step

        steps = new long[numOrigs];
        if(schedulingID == SIMULTANEOUS){
            long step = getRandomStep();
            Arrays.fill(steps, step);
        }else if(schedulingID == FIXED_INTERVAL){
            int range = (int)(endStep - startStep + 1);
//            System.out.printf("%d -> %d -> %d\n", startStep, range, endStep);
            if(numOrigs < range){
                interval = range / numOrigs;
                for(int i=0; i<numOrigs; i++){
                    steps[i] = startStep + interval*i;
                }
            }else{
                long batch = numOrigs / range;
                for(int i=0; i<numOrigs; i++){
                    steps[i] = startStep + i/batch;
                }
            }
        }else if(schedulingID == RANDOM_RANGE){
            for(int i=0; i<numOrigs; i++){
                steps[i] = getRandomStep();
            }
        }
    }

    @Override
    public int getNumTransactions() {
        return alert.getMembers().size() - 1;
    }

    @Override
    public String getType() {
        return "FanInTypology";
    }

    public void sendTransactions(long step, Account acct){
        long alertID = alert.getAlertID();
        boolean isSAR = alert.isSAR();
        float amount = getRandomAmount();  // / origs.size();

        for(int i = 0; i< origList.size(); i++){
            if(steps[i] == step){
                Account orig = origList.get(i);
                sendTransaction(step, amount, orig, bene, isSAR, alertID);
            }
        }
    }
}
