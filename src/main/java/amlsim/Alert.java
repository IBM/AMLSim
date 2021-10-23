package amlsim;

import amlsim.model.aml.AMLTypology;
import paysim.PaySim;

import java.util.*;

/*
 * Group of suspicious transactions and involving accounts as an AML typology
 * Accounts in this class perform suspicious transactions based on the given typology (model)
 */
public class Alert {

    private long alertID;  // Alert identifier
    private List<Account> members;  // Accounts involved in this alert
    private Account mainAccount;   // Main account of this alert
    private AMLTypology model;    // Transaction model
    private AMLSim amlsim;  // AMLSim main object

    Alert(long alertID, AMLTypology model, AMLSim sim){
        this.alertID = alertID;
        this.members = new ArrayList<>();
        this.mainAccount = null;
        this.model = model;
        this.model.setAlert(this);
        this.amlsim = sim;
    }

    /**
     * Add transactions
     * @param step Current simulation step
     */
    void registerTransactions(long step, Account acct){
        if(model.isValidStep(step)){
            model.sendTransactions(step, acct);
        }
    }

    /**
     * Involve an account in this alert
     * @param acct Account object
     */
    void addMember(Account acct){
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

    /**
     * Get the main account
     * @return The main account if exists.
     */
    public Account getMainAccount(){
        return mainAccount;
    }

    /**
     * Set the main account
     * @param account Main account object
     */
    void setMainAccount(Account account){
        this.mainAccount = account;
    }

    public AMLTypology getModel(){
        return model;
    }

    public boolean isSAR(){
        return this.mainAccount != null && this.mainAccount.isSAR();
    }
}

