package amlsim.model.fraud;

import amlsim.Account;

import java.util.*;

public class ScatterGatherModel extends FraudTransactionModel {

    private Account orig = null;  // First sender account (main)
    private Account bene = null;  // Last receiver account
    private List<Account> intermediate = new ArrayList<>();
    private long[] scatterSteps;
    private long[] gatherSteps;

    public ScatterGatherModel(float minAmount, float maxAmount, int startStep, int maxStep) {
        super(minAmount, maxAmount, startStep, maxStep);
    }

    @Override
    public void setSchedule(int modelID) {
        orig = alert.getSubjectAccount();
        for (Account acct : alert.getMembers()) {
            if (acct == orig) {
                continue;
            }
            if (bene == null) {
                bene = acct;
            } else {
                intermediate.add(acct);
            }
        }

        int size = alert.getMembers().size() - 2;
        scatterSteps = new long[size];
        gatherSteps = new long[size];

        long middleStep = (endStep + startStep) / 2;
        for (int i = 0; i < size; i++) {
            scatterSteps[i] = getRandomStepRange(startStep, middleStep);
            gatherSteps[i] = getRandomStepRange(middleStep, endStep);
        }
//        System.out.println(Arrays.toString(scatterSteps));
//        System.out.println(Arrays.toString(gatherSteps));
    }

    @Override
    public int getNumTransactions() {
        int totalMembers = alert.getMembers().size();
        int midMembers = totalMembers - 2;
        return midMembers * 2;
    }

    @Override
    public void sendTransactions(long step, Account acct) {
        long alertID = alert.getAlertID();
        boolean isFraud = alert.isFraud();
        int totalMembers = alert.getMembers().size();
        int midMembers = totalMembers - 2;

//        float scatterAmount = getAmount();
//        float margin = (float) (scatterAmount * 0.1);
//        float gatherAmount = scatterAmount - margin;

        for(int i=0; i<midMembers; i++){
            if(scatterSteps[i] == step){
                float amount = getAmount();
                Account _bene = intermediate.get(i);
                sendTransaction(step, amount, orig, _bene, isFraud, alertID);
//                System.out.println("Scatter " + i + " " + step + " " + amount);
            }else if(gatherSteps[i] == step) {
                float amount = getAmount();
                Account _orig = intermediate.get(i);
                sendTransaction(step, amount, _orig, bene, isFraud, alertID);
//                System.out.println("Gather " + i + " " + step + " " + amount);
            }
        }
    }
}
