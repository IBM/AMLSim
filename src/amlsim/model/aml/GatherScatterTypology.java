package amlsim.model.aml;

import amlsim.Account;

import java.util.*;

/**
 * Gather-Scatter transaction model (Multiple accounts -> fan-in -> main account -> fan-out -> multiple accounts)
 */
public class GatherScatterTypology extends AMLTypology {

    private List<Account> origAccts = new ArrayList<>();
    private List<Account> beneAccts = new ArrayList<>();
    private long[] gatherSteps;
    private long[] scatterSteps;
    private long middleStep;
    private float totalReceivedAmount = 0.0F;
    private float scatterAmount = 0.0F;  // Scatter transaction amount will be defined after gather transactions

    GatherScatterTypology(float minAmount, float maxAmount, int startStep, int endStep) {
        super(minAmount, maxAmount, startStep, endStep);
    }

    @Override
    public void setParameters(int modelID) {
        middleStep = (startStep + endStep) / 2;

        int numSubMembers = alert.getMembers().size() - 1;
        int numOrigMembers = numSubMembers / 2;
        int numBeneMembers = numSubMembers - numOrigMembers;

        gatherSteps = new long[numOrigMembers];
        scatterSteps = new long[numBeneMembers];

        Account mainAcct = alert.getSubjectAccount();
        List<Account> subMembers = new ArrayList<>();
        for (Account acct : alert.getMembers()){
            if(acct != mainAcct){
                subMembers.add(acct);
            }
        }
        assert(numSubMembers == subMembers.size());
        for(int i=0; i<numSubMembers; i++){
            Account acct = subMembers.get(i);
            if(i < numOrigMembers){
                origAccts.add(acct);
            }else{
                beneAccts.add(acct);
            }
        }

        for(int i=0; i<numOrigMembers; i++){
            gatherSteps[i] = getRandomStepRange(startStep, middleStep);
        }
        for(int i=0; i<numBeneMembers; i++){
            scatterSteps[i] = getRandomStepRange(middleStep, endStep);
        }
    }

    @Override
    public int getNumTransactions() {
        return 0;
    }

    @Override
    public void sendTransactions(long step, Account acct) {
        long alertID = alert.getAlertID();
        boolean isSAR = alert.isSAR();

        if(step < middleStep){
            for(int i=0; i<gatherSteps.length; i++){
                if(gatherSteps[i] == step){
                    Account orig = origAccts.get(i);
                    Account bene = alert.getSubjectAccount();
                    float amount = getRandomAmount();
                    sendTransaction(step, amount, orig, bene, isSAR, alertID);
                    totalReceivedAmount += amount;
                }
            }
        }else{
            int numScatters = scatterSteps.length;
            if(step == middleStep){  // Define the amount of scatter transactions
                float margin = totalReceivedAmount * MARGIN_RATIO;
                scatterAmount = Math.max((totalReceivedAmount - margin) / numScatters, minAmount);
            }
            for(int i=0; i<numScatters; i++){
                if(scatterSteps[i] == step){
                    Account orig = alert.getSubjectAccount();
                    Account bene = beneAccts.get(i);
                    sendTransaction(step, scatterAmount, orig, bene, isSAR, alertID);
                }
            }
        }
    }

    @Override
    public String getType() {
        return "GatherScatterTypology";
    }
}

