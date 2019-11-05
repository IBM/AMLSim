package amlsim.model.fraud;

import amlsim.Account;

import java.util.*;

/**
 * Gather-Scatter transaction model (Multiple accounts -> fan-in -> main account -> fan-out -> multiple accounts)
 */
public class GatherScatterModel extends FraudTransactionModel {

    private List<Account> origAccts = new ArrayList<>();
    private List<Account> beneAccts = new ArrayList<>();
    private long[] gatherSteps;
    private long[] scatterSteps;
    private long middleStep;

    public GatherScatterModel(float minAmount, float maxAmount, int startStep, int endStep) {
        super(minAmount, maxAmount, startStep, endStep);
        middleStep = (startStep + endStep) / 2;
    }

    @Override
    public void setParameters(int modelID) {
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
        boolean isSar = alert.isSar();

        if(step < middleStep){
            for(int i=0; i<gatherSteps.length; i++){
                if(gatherSteps[i] == step){
                    Account orig = origAccts.get(i);
                    Account bene = alert.getSubjectAccount();
                    float amount = getAmount();
                    sendTransaction(step, amount, orig, bene, isSar, alertID);
                }
            }
        }else{
            for(int i=0; i<scatterSteps.length; i++){
                if(scatterSteps[i] == step){
                    Account orig = alert.getSubjectAccount();
                    Account bene = beneAccts.get(i);
                    float amount = getAmount();
                    sendTransaction(step, amount, orig, bene, isSar, alertID);
                }
            }
        }
    }
}

