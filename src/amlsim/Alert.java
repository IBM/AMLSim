package amlsim;

import amlsim.model.fraud.FraudTransactionModel;
import paysim.PaySim;

import java.util.*;

/*
 * Group of fraud transactions and involving accounts
 * Fraud accounts in this class perform suspicious transactions based on a fraud rule
 */
public class Alert {

    private long alertID;  // Alert identifier
    private List<Account> members;  // Accounts involved in this alert
    private Account subject;   // Main account of the fraud alert
    private FraudTransactionModel model;    // Transaction model
    private AMLSim amlsim;  // AMLSim main object

    public Alert(long alertID, FraudTransactionModel model, AMLSim sim){
        this.alertID = alertID;
        this.members = new ArrayList<>();
        this.subject = null;
        this.model = model;
        this.model.setAlert(this);
        this.amlsim = sim;
    }

    /**
     * Add transactions
     * @param step Current simulation step
     */
    public void registerTransactions(long step, Account acct){
        if(model.isValidStep(step)){
            model.sendTransactions(step, acct);
        }
    }

    /**
     * Involve an account in this alert
     * @param acct Account object
     */
    public void addMember(Account acct){
        this.members.add(acct);
        acct.addAlertGroup(this);
    }

    /**
     * Get main AMLSim object
     * @return AMLSim object
     */
    public PaySim getSimulator(){
        return amlsim;
    }

    /**
     * Get alert identifier as long type
     * @return Alert identifier
     */
    public long getAlertID(){
        return alertID;
    }

    /**
     * Get member list of the alert
     * @return Alert account list
     */
    public List<Account> getMembers(){
        return members;
    }

    public Account getSubjectAccount(){
        return subject;
    }

    public void setSubjectAccount(FraudAccount fraudster){
        this.subject = fraudster;
    }

    public FraudTransactionModel getModel(){
        return model;
    }

    public boolean isFraud(){
        return this.subject != null;  // The alert group is fraud if and only if a subject account exists
    }
}

