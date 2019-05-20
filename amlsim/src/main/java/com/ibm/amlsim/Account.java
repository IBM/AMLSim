package com.ibm.amlsim;

import com.ibm.amlsim.model.*;
import com.ibm.amlsim.model.cash.CashInModel;
import com.ibm.amlsim.model.cash.CashOutModel;
import com.ibm.amlsim.model.normal.*;
import paysim.*;
import sim.engine.SimState;
import sim.engine.Steppable;
import java.util.*;

public class Account extends Client implements Steppable {

//	protected long id;
    protected String id;

    protected Map<String, String> extraAttributes;
	protected AbstractTransactionModel model;
	protected CashInModel cashInModel;
	protected CashOutModel cashOutModel;
	private boolean caseSubject = false;
	private Random rand = new Random();
	private Branch branch = null;
//	private Map<Long, Account> origs = new HashMap<>();  // Sender Client ID --> Client Object
//	private Map<Long, Account> dests = new HashMap<>();  // Receiver Client ID --> Client Object
    private Map<String, Account> origs = new HashMap<>();  // Sender Client ID --> Client Object
    private Map<String, Account> dests = new HashMap<>();  // Receiver Client ID --> Client Object

    private Account prevOrig = null;  // Previous sender Client
	private Account prevDest = null;  // Previous receiver Client
	List<Alert> alerts = new ArrayList<>();
//	private Map<Long, String> tx_types = new HashMap<>();  // Receiver Client ID --> Transaction Type
    private Map<String, String> tx_types = new HashMap<>();  // Receiver Client ID --> Transaction Type

	private static List<String> all_tx_types = new ArrayList<>();

	private ArrayList<ActionProbability> probList;
	private ArrayList<String> paramFile = new ArrayList<>();
	private CurrentStepHandler stepHandler = null;

	protected long startStep = 0;
	protected long endStep = 0;


	public Account(){
//		this.id = 0;
        this.id = "-";
		this.model = null;
	}

	/**
	 * Constructor of the account object
	 * @param id Client ID
	 * @param modelID Transaction model ID (int value)
	 * @param init_balance Initial account balance
	 * @param start Start step
	 * @param end End step
	 */
//	public Account(long id, int modelID, float init_balance, long start, long end){
    public Account(String id, int modelID, float init_balance, long start, long end, Map<String, String> attrs){
		this.id = id;
		this.startStep = start;
		this.endStep = end;
		this.extraAttributes = attrs;

		switch(modelID){
			case AbstractTransactionModel.SINGLE: this.model = new SingleTransactionModel(); break;
			case AbstractTransactionModel.FANOUT: this.model = new FanOutTransactionModel(); break;
			case AbstractTransactionModel.FANIN: this.model = new FanInTransactionModel(); break;
			case AbstractTransactionModel.MUTUAL: this.model = new MutualTransactionModel(); break;
			case AbstractTransactionModel.FORWARD: this.model = new ForwardTransactionModel(); break;
			case AbstractTransactionModel.PERIODICAL: this.model = new PeriodicalTransactionModel(); break;
			default: System.err.println("Unknown model ID: " + modelID); this.model = new EmptyModel(); break;
		}
		this.model.setAccount(this);
		this.model.setParameters(init_balance, start, end);

		this.cashInModel = new CashInModel();
		this.cashInModel.setAccount(this);
		this.cashInModel.setParameters(init_balance, start, end);

		this.cashOutModel = new CashOutModel();
		this.cashOutModel.setAccount(this);
		this.cashOutModel.setParameters(init_balance, start, end);
	}

	public String getAttrValue(String name){
        return this.extraAttributes.get(name);
    }

	public long getStartStep(){
		return this.startStep;
	}
	public long getEndStep(){
		return this.endStep;
	}

	public void setCase(boolean flag){
		this.caseSubject = flag;
	}

	public boolean isCase(){
		return this.caseSubject;
	}

	public void setBranch(Branch branch){
		this.branch = branch;
	}

	public Branch getBranch(){
		return this.branch;
	}

	public void addDest(Account dest){
		dests.put(dest.id, dest);
		dest.origs.put(this.id, this);
	}

	public void addTxType(Account dest, String ttype){
		this.tx_types.put(dest.id, ttype);
		all_tx_types.add(ttype);
	}

	public String getTxType(Account dest){
//		long destID = dest.id;
        String destID = dest.id;

		if(this.tx_types.containsKey(destID)){
			return tx_types.get(destID);
		}else if(!this.tx_types.isEmpty()){
			List<String> values = new ArrayList<>(this.tx_types.values());
			return values.get(rand.nextInt(values.size()));
		}else{
			return Account.all_tx_types.get(rand.nextInt(Account.all_tx_types.size()));
		}
	}

	/**
	 * Get previous (origin) accounts
	 * @return Origin account list
	 */
	public List<Account> getOrigs(){
		return new ArrayList<>(this.origs.values());
	}

	/**
	 * Get next (destination) accounts
	 * @return Destination account list
	 */
	public List<Account> getDests(){
		return new ArrayList<>(this.dests.values());
	}

	/**
	 * Register this account to the specified alert group
	 * @param ag Alert group
	 */
	public void addAlertGroup(Alert ag){
		this.alerts.add(ag);
	}

	/**
	 * Perform transactions
	 * @param state AMLSim object
	 */
	@Override
	public void step(SimState state) {
		long currentStep = state.schedule.getSteps();  // Current simulation step
		if(currentStep < this.startStep || this.endStep < currentStep){
			return;  // Skip transactions if this account is not active
		}
		handleAction(state);
	}

//	/**
//	 * @deprecated This method is obsolete because of performance overhead
//	 * @param step Current simulation step
//	 * @return Transaction list
//	 */
//	public List<AMLTransaction> getTransaction(long step){
//		if(AMLSim.TX_OPT)return null;
//
//		List<AMLTransaction> txs =  this.tx_repository.get(step);
//		this.tx_repository.remove(step);
//		return txs;
//	}


	public void handleAction(SimState state) {
		AMLSim amlsim = (AMLSim) state;
		long step = state.schedule.getSteps();
		for(Alert ag : alerts){
			ag.registerTransactions(step);
		}

		this.model.sendTransaction(step);
//		handleTransaction(amlsim);
		handleCashTransaction(amlsim);
	}

	/**
	 * Perform cash transactions (deposit and withdrawal)
	 * @param amlsim AMLSim object
	 */
	private void handleCashTransaction(AMLSim amlsim){
		long step = amlsim.schedule.getSteps();
		this.cashInModel.sendTransaction(step);
		this.cashOutModel.sendTransaction(step);
	}

//	/**
//	 * @deprecated This method is obsolete because of performance problem
//	 * @param amlsim AMLSimulator object
//	 * @return true
//	 */
//	boolean handleTransaction(AMLSim amlsim) {
//		long step = amlsim.schedule.getSteps();
//
//		List<AMLTransaction> txs = this.getTransaction(step);  // Get a registered transaction
//		if(txs == null) {
//			txs = this.model.sendTransaction(step);
//		}
//		if(txs == null || txs.isEmpty()){
//			return false;
//		}

//		for(AMLTransaction tx : txs) {
//			if(tx == null)continue;
//
//			double amount = tx.getAmount();
//			Account dstBefore = tx.getClientDestBefore();
//			Account dstAfter = new Account();
//			dstAfter.setAccount(dstBefore);
//			dstAfter.deposit(amount);
//
//			Account srcBefore = new Account();
//			srcBefore.setAccount(this);
//			this.withdraw(amount);
//			Account srcAfter = new Account();
//			srcAfter.setAccount(this);
//			dstAfter.deposit(amount);
//
//			long destID = dstBefore.id;
//			Account dest = dests.get(destID);
//			this.prevDest = dest;
//			dest.prevOrig = this;
//
//			tx.setClientOrigBefore(srcBefore);
//			tx.setClientOrigAfter(srcAfter);
//			tx.setClientDestAfter(dstAfter);
//			tx.setClientDestBefore(dstBefore);
//			tx.setFraud(false);
//			amlsim.getTrans().add(tx);
//		}
//		return true;
//	}


	/**
	 * Get the previous origin (sender) account
	 * @return Previous sender account object
	 */
	public Account getPrevOrig(){
		return prevOrig;
	}

	public Account getPrevDest(){
		return prevDest;
	}

	public void setClient(Account c){
		this.id = c.getID();
		this.setBalance(c.getBalance());
		this.setCurrency(c.getCurrency());
		this.setName(c.getName());
		this.setNumDeposits(c.getNumDeposits());
		this.setNumTransfers(c.getNumTransfers());
		this.setNumWithdraws(c.getNumWithdraws());
		this.origs = c.origs;
		this.dests = c.dests;
	}

	public String getName() {
//		return Long.toString(this.id);
        return this.id;
	}

	/**
	 * Get the account identifier as long
	 * @return Account identifier
	 */
    public String getID(){
        return this.id;
    }
//	public long getID(){
//		return this.id;
//	}

	/**
	 * Get the account identifier as String
	 * @return Account identifier
	 */
	public String toString() {
		return "C" + this.id;
	}

	public ArrayList<ActionProbability> getProbList() {
		return probList;
	}

	public void setProbList(ArrayList<ActionProbability> probList) {
		this.probList = probList;
	}

	public ArrayList<String> getParamFile() {
		return paramFile;
	}

	public void setParamFile(ArrayList<String> paramFile) {
		this.paramFile = paramFile;
	}

	public CurrentStepHandler getStepHandler() {
		return stepHandler;
	}

	public void setStepHandler(CurrentStepHandler stepHandler) {
		this.stepHandler = stepHandler;
	}
}
