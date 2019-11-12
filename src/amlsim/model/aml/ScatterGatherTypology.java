package amlsim.model.aml;

import amlsim.Account;

import java.util.*;

/**
 * Scatter-Gather transaction model (Main originator account -> fan-out -> multiple accounts -> fan-in -> single account)
 */
public class ScatterGatherTypology extends AMLTypology {

    private Account orig = null;  // The first sender (main) account
    private Account bene = null;  // The last beneficiary account
    private List<Account> intermediate = new ArrayList<>();
    private long[] scatterSteps;
    private long[] gatherSteps;
    private float scatterAmount;
    private float gatherAmount;

    ScatterGatherTypology(float minAmount, float maxAmount, int startStep, int maxStep) {
        super(minAmount, maxAmount, startStep, maxStep);
    }

    @Override
    public void setParameters(int modelID) {
        scatterAmount = maxAmount;
        float margin = scatterAmount * marginRatio;
        gatherAmount = Math.max(scatterAmount - margin, minAmount);

        orig = alert.getMainAccount();
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
        boolean isSAR = alert.isSAR();
        int numTotalMembers = alert.getMembers().size();
        int numMidMembers = numTotalMembers - 2;

        for(int i=0; i<numMidMembers; i++){
            if(scatterSteps[i] == step){
                Account _bene = intermediate.get(i);
                sendTransaction(step, scatterAmount, orig, _bene, isSAR, alertID);
            }else if(gatherSteps[i] == step) {
                Account _orig = intermediate.get(i);
                sendTransaction(step, gatherAmount, _orig, bene, isSAR, alertID);
            }
        }
    }

    @Override
    public String getType() {
        return "ScatterGatherTypology";
    }
}
