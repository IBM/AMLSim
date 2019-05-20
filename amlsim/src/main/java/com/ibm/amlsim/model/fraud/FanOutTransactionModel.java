//
// Note: No specific bank models are used for this fraud transaction model class.
//

package com.ibm.amlsim.model.fraud;

import com.ibm.amlsim.Account;

import java.util.*;

/**
 * The subject account sends money to multiple members
 */
public class FanOutTransactionModel extends FraudTransactionModel {

    // Sender and receivers
    private Account orig;
    private List<Account> dests = new ArrayList<>();

    // Transaction schedule
    private int schedule_mode;
    private long[] steps;
    public static final int SIMULTANEOUS = 1;
    public static final int FIXED_INTERVAL = 2;
    public static final int RANDOM_RANGE = 3;

    public FanOutTransactionModel(float minAmount, float maxAmount, int minStep, int maxStep){
        super(minAmount, maxAmount, minStep, maxStep);
    }

    public void setSchedule(int modelID){
        this.schedule_mode = modelID;

        // Set members
        List<Account> members = alert.getMembers();
        orig = alert.isFraud() ? alert.getSubjectAccount() : members.get(0);
        for(Account dest : members){
            if(orig != dest) dests.add(dest);
        }

        // Set schedule
        int numDests = dests.size();
        steps = new long[numDests];
        if(schedule_mode == SIMULTANEOUS){
            long step = getRandomStep();
            Arrays.fill(steps, step);
        }else if(schedule_mode == FIXED_INTERVAL){
            long range = endStep - startStep + 1;
            if(numDests < range){
                long interval = range / numDests;
                for(int i=0; i<numDests; i++){
                    steps[i] = startStep + interval*i;
                }
            }else{
                long batch = numDests / range;
                for(int i=0; i<numDests; i++){
                    steps[i] = startStep + i/batch;
                }
            }
        }else if(schedule_mode == RANDOM_RANGE){
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
    public void sendTransactions(long step) {
        long alertID = alert.getAlertID();
        boolean isFraud = alert.isFraud();
        float amount = getAmount() / dests.size();

        for(int i=0; i<dests.size(); i++){
            if(steps[i] == step){
                Account dest = dests.get(i);
                sendTransaction(step, amount, orig, dest, isFraud, alertID);
            }
        }
    }

//    @Override
//    public Collection<AMLTransaction> sendTransactions(long step) {
//        ArrayList<AMLTransaction> txs = new ArrayList<>();
//        List<AMLClient> members = this.alert.getMembers();
//
//        AMLClient orig = members.get(0);
//        if(alert.isFraud()) {    // Fraud alert
//            orig = this.alert.getSubjectAccount();
//        }else{    // Alert alert (not fraud)
//            int max_degree = 0;
//            for(AMLClient c : members){
//                int degree = c.getDests().size();
//                if(degree > max_degree){
//                    orig = c;
//                    max_degree = degree;
//                }
//            }
//        }
//
//        List<AMLClient> dests = orig.getDests();
//        float amount = getAmount() / dests.size();
//
//        long alertID = alert.getAlertID();
//        boolean isFraud = alert.isFraud();
//
//        for(AMLClient dest : dests){
//            AMLTransaction tx = sendTransaction(step, amount, orig, dest);
//            tx.setAlertID(alertID);
//            tx.setFraud(isFraud);
//            txs.add(tx);
//        }
//        return txs;
//    }
}
