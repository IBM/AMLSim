package amlsim;

import amlsim.model.*;
import amlsim.model.cash.CashInModel;
import amlsim.model.cash.CashOutModel;
import amlsim.model.normal.*;
import paysim.*;
import sim.engine.SimState;
import sim.engine.Steppable;
import java.util.*;

public class Account extends Client implements Steppable {

    protected String id;

    private Map<String, String> extraAttributes;
	protected AbstractTransactionModel model;
	private CashInModel cashInModel;
	private CashOutModel cashOutModel;
	private boolean isSAR = false;
	private Random rand = new Random();
	private Branch branch = null;
    private Map<String, Account> origAccts = new HashMap<>();  // Originator account ID --> Account object
    private Map<String, Account> beneAccts = new HashMap<>();  // Beneficiary account ID --> Account object
	private String bankID = "";  // Bank ID

    private Account prevOrig = null;  // Previous originator account
	List<Alert> alerts = new ArrayList<>();
    private Map<String, String> tx_types = new HashMap<>();  // Receiver Client ID --> Transaction Type

	private static List<String> all_tx_types = new ArrayList<>();

	private ArrayList<ActionProbability> probList;
	private ArrayList<String> paramFile = new ArrayList<>();
	private CurrentStepHandler stepHandler = null;

	protected long startStep = 0;
	protected long endStep = 0;


	public Account(){
        this.id = "-";
		this.model = null;
	}

	/**
	 * Constructor of the account object
	 * @param id Account ID
	 * @param modelID Transaction model ID (int value)
     * @param interval Default transaction interval
	 * @param initBalance Initial account balance
	 * @param start Start step
	 * @param end End step
	 * @param attrs Other attributes
	 */
    public Account(String id, int modelID, int interval, float initBalance, long start, long end, Map<String, String> attrs){
		this.id = id;
		this.startStep = start;
		this.endStep = end;
		this.extraAttributes = attrs;

		switch(modelID){
			case AbstractTransactionModel.SINGLE: this.model = new SingleTransactionModel(); break;
			case AbstractTransactionModel.FAN_OUT: this.model = new FanOutTransactionModel(); break;
			case AbstractTransactionModel.FAN_IN: this.model = new FanInTransactionModel(); break;
			case AbstractTransactionModel.MUTUAL: this.model = new MutualTransactionModel(); break;
			case AbstractTransactionModel.FORWARD: this.model = new ForwardTransactionModel(); break;
			case AbstractTransactionModel.PERIODICAL: this.model = new PeriodicalTransactionModel(); break;
			default: System.err.println("Unknown model ID: " + modelID); this.model = new EmptyModel(); break;
		}
		this.model.setAccount(this);
		this.model.setParameters(interval, initBalance, start, end);

		this.cashInModel = new CashInModel();
		this.cashInModel.setAccount(this);
		this.cashInModel.setParameters(interval, initBalance, start, end);

		this.cashOutModel = new CashOutModel();
		this.cashOutModel.setAccount(this);
		this.cashOutModel.setParameters(interval, initBalance, start, end);
	}

	/**
	 * Constructor with bank ID
	 * @param id Account ID
	 * @param modelID　Transaction model ID
	 * @param interval Default transaction interval
	 * @param initBalance Initial account balance
	 * @param start Start step
	 * @param end End step
	 * @param bankID Bank ID
	 * @param attrs Other attributes
	 */
	public Account(String id, int modelID, int interval, float initBalance, long start, long end, String bankID, Map<String, String> attrs){
    	this(id, modelID, interval, initBalance, start, end, attrs);
    	this.bankID = bankID;
	}

	public String getBankID() {
		return this.bankID;
	}

//	public String getAttrValue(String name){
//        return this.extraAttributes.get(name);
//    }

	public long getStartStep(){
		return this.startStep;
	}
	public long getEndStep(){
		return this.endStep;
	}

	void setSAR(boolean flag){
		this.isSAR = flag;
	}

	public boolean isSAR(){
		return this.isSAR;
	}

	void setBranch(Branch branch){
		this.branch = branch;
	}

	public Branch getBranch(){
		return this.branch;
	}

	public void addDest(Account dest){
		beneAccts.put(dest.id, dest);
		dest.origAccts.put(this.id, this);
	}

	void addTxType(Account dest, String ttype){
		this.tx_types.put(dest.id, ttype);
		all_tx_types.add(ttype);
	}

	public String getTxType(Account dest){
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
	 * Get previous (originator) accounts
	 * @return Originator account list
	 */
	public List<Account> getOrigList(){
		return new ArrayList<>(this.origAccts.values());
	}

	/**
	 * Get next (beneficiary) accounts
	 * @return Beneficiary account list
	 */
	public List<Account> getBeneList(){
		return new ArrayList<>(this.beneAccts.values());
	}

	/**
	 * Register this account to the specified alert group
	 * @param ag Alert group
	 */
	void addAlertGroup(Alert ag){
		this.alerts.add(ag);
	}

	/**
	 * Perform transactions
	 * @param state AMLSim object
	 */
	@Override
	public void step(SimState state) {
		long currentStep = state.schedule.getSteps();  // Current simulation step
        long start = this.startStep >= 0 ? this.startStep : 0;
        long end = this.endStep > 0 ? this.endStep : AMLSim.getNumOfSteps();
		if(currentStep < start || end < currentStep){
			return;  // Skip transactions if this account is not active
		}
		handleAction(state);
	}


	public void handleAction(SimState state) {
		AMLSim amlsim = (AMLSim) state;
		long step = state.schedule.getSteps();
		for(Alert ag : alerts){
            if(this == ag.getMainAccount()){
                ag.registerTransactions(step, this);
            }
		}

		this.model.sendTransaction(step);
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

    public AbstractTransactionModel getModel(){
	    return model;
    }

	/**
	 * Get the previous originator account
	 * @return Previous originator account objects
	 */
	public Account getPrevOrig(){
		return prevOrig;
	}

	public String getName() {
        return this.id;
	}

	/**
	 * Get the account identifier as long
	 * @return Account identifier
	 */
    public String getID(){
        return this.id;
    }

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
