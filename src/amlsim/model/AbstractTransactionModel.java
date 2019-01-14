package amlsim.model;

import amlsim.Account;
import amlsim.AMLSim;

/**
 * Base class of transaction models
 */
public abstract class AbstractTransactionModel {

    // Transaction model ID
    public static final int SINGLE = 0;  // Make a single transaction to each neighbor account
//    public static final int COARSE = 1;
//    public static final int FINE = 2;
    public static final int FANOUT = 1;  // Make transactions to all neighbor accounts
    public static final int FANIN = 2;
    public static final int MUTUAL = 3;
    public static final int FORWARD = 4;
    public static final int PERIODICAL = 5;

    protected Account account;  // Account object
    protected float balance;  // Current balance
    protected long startStep;  // The first step of transactions
    protected long endStep;  // The end step of transactions

    public void setAccount(Account account){
        this.account = account;
    }

    /**
     * Return transaction type
     * @return Transaction type name
     */
    public abstract String getType();

    /**
     * Create transactions
     * @param step Current simulation step
     */
    public abstract void sendTransaction(long step);

    /**
     * Set initial parameters
     * This method will be called when the account is initialized and receives money
     * @param balance Initial balance
     * @param start Start simulation step (any transactions cannot be carried out before this step)
     * @param end End step (any transactions cannot be carried out after this step)
     */
    public void setParameters(float balance, long start, long end){
        this.balance = balance;
        this.startStep = start;
        this.endStep = end;
    }

    /**
     * Generate and register a transaction (for fraud transactions)
     * @param step Current simulation step
     * @param amount Transaction amount
     * @param orig Origin account
     * @param dest Destination account
     * @param isFraud Whether this transaction is fraud
     * @param aid Alert ID
     */
    protected void sendTransaction(long step, float amount, Account orig, Account dest, boolean isFraud, long aid){
        String ttype = orig.getTxType(dest);
        AMLSim.handleTransaction(step, ttype, amount, orig, dest, isFraud, aid);
    }

    /**
     * Generate and register a transaction (for cash transactions)
     * @param step Current simulation step
     * @param amount Transaction amount
     * @param orig Origin account
     * @param dest Destination account
     * @param ttype Transaction type
     */
    protected void sendTransaction(long step, float amount, Account orig, Account dest, String ttype){
        AMLSim.handleTransaction(step, ttype, amount, orig, dest, false, -1);
    }

    /**
     * Generate and register a transaction (for normal transactions)
     * @param step Current simulation step
     * @param amount Transaction amount
     * @param orig Origin account
     * @param dest Destination account
     */
    protected void sendTransaction(long step, float amount, Account orig, Account dest){
//        if(AMLSim.TX_OPT){  // Do not create AMLTransaction objects
            sendTransaction(step, amount, orig, dest, false, -1);
//        }

        // Create minimal transaction object from this account to the dest account
//        String ttype = orig.getTxType(dest);
//        AMLTransaction tx = new AMLTransaction(step, orig, (short)1, amount, ttype);
//
//        Account destBefore = new Account();
//        destBefore.setAccount(dest);
//        tx.setClientDestBefore(destBefore);
//
//        tx.setDay(orig.getCurrDay());
//        tx.setHour(orig.getCurrHour());
    }

    /**
     * Generate and register a transaction (for normal transactions)
     * @param step Current simulation step
     * @param amount Transaction amount
     * @param dest Destination account
     */
    protected void sendTransaction(long step, float amount, Account dest){
        this.sendTransaction(step, amount, this.account, dest);
    }

//    public abstract void sent();
}
