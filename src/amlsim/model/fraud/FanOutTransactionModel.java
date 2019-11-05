//
// Note: No specific bank models are used for this fraud transaction model class.
//

package amlsim.model.fraud;

import amlsim.Account;

import java.util.*;

/**
 * The subject account sends money to multiple members
 */
public class FanOutTransactionModel extends FraudTransactionModel {

    // Sender and receivers
    private Account orig;
    private List<Account> dests = new ArrayList<>();

    private long[] steps;
    public static final int SIMULTANEOUS = 1;
    public static final int FIXED_INTERVAL = 2;
    public static final int RANDOM_RANGE = 3;

    public FanOutTransactionModel(float minAmount, float maxAmount, int minStep, int maxStep){
        super(minAmount, maxAmount, minStep, maxStep);
    }

    public int getNumTransactions(){
        return alert.getMembers().size() - 1;
    }

    public void setParameters(int scheduleID){
        // Set members
        List<Account> members = alert.getMembers();
        orig = alert.isSar() ? alert.getSubjectAccount() : members.get(0);
        for(Account dest : members){
            if(orig != dest) dests.add(dest);
        }

        // Set schedule
        int numDests = dests.size();
        int totalStep = (int)(endStep - startStep + 1);
        int defaultInterval = totalStep / numDests;
        this.startStep = generateStartStep(defaultInterval);  //  decentralize the first transaction step

        steps = new long[numDests];
        if(scheduleID == SIMULTANEOUS){
            long step = getRandomStep();
            Arrays.fill(steps, step);
        }else if(scheduleID == FIXED_INTERVAL){
            int range = (int)(endStep - startStep + 1);
            if(numDests < range){
                interval = range / numDests;
                for(int i=0; i<numDests; i++){
                    steps[i] = startStep + interval*i;
                }
            }else{
                long batch = numDests / range;
                for(int i=0; i<numDests; i++){
                    steps[i] = startStep + i/batch;
                }
            }
        }else if(scheduleID == RANDOM_RANGE){
            for(int i=0; i<numDests; i++){
                steps[i] = getRandomStep();
            }
        }
    }

    @Override
    public String getType() {
        return "FanOutFraud";
    }

    @Override
    public void sendTransactions(long step, Account acct) {
        if(!orig.getID().equals(acct.getID())){
            return;
        }
        long alertID = alert.getAlertID();
        boolean isFraud = alert.isSar();
        float amount = getAmount() / dests.size();

        for(int i=0; i<dests.size(); i++){
            if(steps[i] == step){
                Account dest = dests.get(i);
                sendTransaction(step, amount, orig, dest, isFraud, alertID);
            }
        }
    }
}
