package amlsim.model;

import amlsim.Account;
import amlsim.AccountGroup;
import amlsim.AMLSim;

/**
 * Base class of transaction models
 */
public abstract class AbstractTransactionModel {

    // Transaction model ID
    public static final String SINGLE = "single";  // Make a single transaction to each neighbor account
    public static final String FAN_OUT = "fan_out";  // Send money to all neighbor accounts
    public static final String FAN_IN = "fan_in";  // Receive money from neighbor accounts
    public static final String MUTUAL = "mutual";
    public static final String FORWARD = "forward";
    public static final String PERIODICAL = "periodical";

//    protected static Random rand = new Random(AMLSim.getSeed());

    protected AccountGroup accountGroup;  // Account group object
    protected int interval = 1; // Default transaction interval
    protected long startStep = -1;  // The first step of transactions
    protected long endStep = -1;  // The end step of transactions
    protected boolean isSAR = false;

    /**
     * Get the assumed number of transactions in this simulation
     * @return Number of total transactions
     */
    public int getNumberOfTransactions(){
        return (int)AMLSim.getNumOfSteps() / interval;
    }
    
    /**
     * Set an account object group which has this model
     * 
     * @param accountGroup account group object
     */
    public void setAccountGroup(AccountGroup accountGroup) {
        this.accountGroup = accountGroup;
    }

    /**
     * Get the simulation step range as the period when this model is valid
     * If "startStep" and/or "endStep" is undefined (negative), it returns the largest range
     * @return The total number of simulation steps
     */
    public int getStepRange(){
        long st = startStep >= 0 ? startStep : 0;
        long ed = endStep > 0 ? endStep : AMLSim.getNumOfSteps();
        return (int)(ed - st + 1);
    }

    /**
     * Get transaction model name
     * @return Transaction model name
     */
    public abstract String getModelName();

    
    /**
     * Generate the start transaction step (to decentralize transaction distribution)
     * @param range Simulation step range
     * @return random int value [0, range-1]
     */
    protected static int generateStartStep(int range){
//        return rand.nextInt(range);
        return AMLSim.getRandom().nextInt(range);
    }

    /**
     * Set initial parameters
     * This method will be called when the account is initialized
     * @param interval Transaction interval
     * @param start Start simulation step (It never makes any transactions before this step)
     * @param end End simulation step (It never makes any transactions after this step)
     */
    public void setParameters(int interval, long start, long end){
        this.interval = interval;
        setParameters(start, end);
    }
    
    /**
     * Set initial parameters of the transaction model (for AML typology models)
     * @param start Start simulation step
     * @param end End simulation step
     */
    public void setParameters(long start, long end){
        this.startStep = start;
        this.endStep = end;
    }

    /**
     * The new workhorse method.
     * @param step
     * @param account
     */
    public abstract void sendTransactions(long step, Account account);

    /**
     * Generate and register a transaction (for alert transactions)
     * @param step Current simulation step
     * @param amount Transaction amount
     * @param orig Origin account
     * @param dest Destination account
     * @param isSAR Whether this transaction is SAR
     * @param alertID Alert ID
     */
    protected void makeTransaction(long step, double amount, Account orig, Account dest, boolean isSAR, long alertID){
        if(amount <= 0){  // Invalid transaction amount
           // AMLSim.getLogger().warning("Warning: invalid transaction amount: " + amount);
            return;
        }
        String ttype = orig.getTxType(dest);
        if(isSAR) {
            AMLSim.getLogger().fine("Handle transaction: " + orig.getID() + " -> " + dest.getID());
        }
        AMLSim.handleTransaction(step, ttype, amount, orig, dest, isSAR, alertID);
    }

    /**
     * Generate and register a transaction (for cash transactions)
     * @param step Current simulation step
     * @param amount Transaction amount
     * @param orig Origin account
     * @param dest Destination account
     * @param ttype Transaction type
     */
    protected void makeTransaction(long step, float amount, Account orig, Account dest, String ttype){
        AMLSim.handleTransaction(step, ttype, amount, orig, dest, false, -1);
    }

    /**
     * Generate and register a transaction (for normal transactions)
     * @param step Current simulation step
     * @param amount Transaction amount
     * @param orig Origin account
     * @param dest Destination account
     */
    protected void makeTransaction(long step, double amount, Account orig, Account dest){
        makeTransaction(step, amount, orig, dest, false, -1);
    }
}
