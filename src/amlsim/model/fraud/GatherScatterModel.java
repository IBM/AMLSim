package amlsim.model.fraud;

import amlsim.Account;

import java.util.*;

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
    public void setSchedule(int modelID) {
        int numSubAccts = alert.getMembers().size() - 1;
        int numOrigAccts = numSubAccts / 2;
        int numBeneAccts = numSubAccts - numOrigAccts;

        gatherSteps = new long[numOrigAccts];
        scatterSteps = new long[numBeneAccts];

        Account mainAcct = alert.getSubjectAccount();
        List<Account> subMembers = new ArrayList<>();
        for (Account acct : alert.getMembers()){
            if(acct != mainAcct){
                subMembers.add(acct);
            }
        }
        assert(numSubAccts == subMembers.size());
        for(int i=0; i<numSubAccts; i++){
            Account acct = subMembers.get(i);
            if(i < numOrigAccts){
                origAccts.add(acct);
            }else{
                beneAccts.add(acct);
            }
        }

        for(int i=0; i<numOrigAccts; i++){
            gatherSteps[i] = getRandomStepRange(startStep, middleStep);
        }
        for(int i=0; i<numBeneAccts; i++){
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
        boolean isFraud = alert.isFraud();

        if(step < middleStep){
            for(int i=0; i<gatherSteps.length; i++){
                if(gatherSteps[i] == step){
                    Account orig = origAccts.get(i);
                    Account bene = alert.getSubjectAccount();
                    float amount = getAmount();
                    sendTransaction(step, amount, orig, bene, isFraud, alertID);
                }
            }
        }else{
            for(int i=0; i<scatterSteps.length; i++){
                if(scatterSteps[i] == step){
                    Account orig = alert.getSubjectAccount();
                    Account bene = beneAccts.get(i);
                    float amount = getAmount();
                    sendTransaction(step, amount, orig, bene, isFraud, alertID);
                }
            }
        }
    }
}

