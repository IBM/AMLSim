//
// Note: No specific bank models are used for this fraud transaction model class.
//

package com.ibm.amlsim.model.fraud;

import com.ibm.amlsim.Account;

import java.util.*;

/**
 * Multiple accounts send money to the subject account
 */
public class FanInTransactionModel extends FraudTransactionModel {

    // Senders and receiver
    private Account dest;  // The destination (receiver) account
    private List<Account> origs = new ArrayList<>();  // The origin (sender) accounts

    // Transaction schedule
    private int schedule_mode;
    private long[] steps;
    public static final int SIMULTANEOUS = 1;
    public static final int FIXED_INTERVAL = 2;
    public static final int RANDOM_RANGE = 3;

    public FanInTransactionModel(float minAmount, float maxAmount, int start, int end){
        super(minAmount, maxAmount, start, end);
//        System.out.println(start + " " + end);
    }

    public void setSchedule(int modelID){
        this.schedule_mode = modelID;

        // Set alert members
        List<Account> members = alert.getMembers();
        dest = alert.isFraud() ? alert.getSubjectAccount() : members.get(0);  // The subject account is the receiver
        for(Account orig : members){  // The rest of accounts are senders
            if(orig != dest) origs.add(orig);
        }

        // Set transaction schedule
        int numOrigs = origs.size();
        steps = new long[numOrigs];
        if(schedule_mode == SIMULTANEOUS){
            long step = getRandomStep();
            Arrays.fill(steps, step);
        }else if(schedule_mode == FIXED_INTERVAL){
            long range = endStep - startStep + 1;
            if(numOrigs < range){
                long interval = range / numOrigs;
                for(int i=0; i<numOrigs; i++){
                    steps[i] = startStep + interval*i;
                }
            }else{
                long batch = numOrigs / range;
                for(int i=0; i<numOrigs; i++){
                    steps[i] = startStep + i/batch;
                }
            }
        }else if(schedule_mode == RANDOM_RANGE){
            for(int i=0; i<numOrigs; i++){
                steps[i] = getRandomStep();
            }
        }
    }

    @Override
    public String getType() {
        return "FanInFraud";
    }

    public void sendTransactions(long step){
        long alertID = alert.getAlertID();
        boolean isFraud = alert.isFraud();
        float amount = getAmount() / origs.size();

        for(int i=0; i<origs.size(); i++){
            if(steps[i] == step){
                Account orig = origs.get(i);
                sendTransaction(step, amount, orig, dest, isFraud, alertID);
            }
        }
    }

//    @Override
//    public Collection<AMLTransaction> sendTransactions(long step) {
//        ArrayList<AMLTransaction> txs = new ArrayList<>();
//        List<AMLClient> members = this.alert.getMembers();
//
//        AMLClient dest = members.get(0);
//        if(alert.isFraud()) {    // Fraud alert
//            dest = this.alert.getSubjectAccount();
//        }else{    // Alert alert (not fraud)
//            int max_degree = 0;
//            for(AMLClient c : members){
//                int degree = c.getOrigs().size();
//                if(degree > max_degree){
//                    dest = c;
//                    max_degree = degree;
//                }
//            }
//        }
//        List<AMLClient> origs = dest.getOrigs();
//        long alertID = alert.getAlertID();
//        boolean isFraud = alert.isFraud();
//        for(AMLClient orig : origs){
//            float amount = getAmount();
//            AMLTransaction tx = sendTransaction(step, amount, orig, dest);
//            tx.setAlertID(alertID);
//            tx.setFraud(isFraud);
//            txs.add(tx);
//        }
//
//        return txs;
//    }
}
