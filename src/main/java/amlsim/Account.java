package amlsim;

import amlsim.model.*;
import amlsim.model.cash.CashInModel;
import amlsim.model.cash.CashOutModel;
import sim.engine.SimState;
import sim.engine.Steppable;
import java.util.*;

public class Account implements Steppable {

    protected String id;

	protected CashInModel cashInModel;
	protected CashOutModel cashOutModel;
	protected boolean isSAR = false;
	private Branch branch = null;
	private Set<String> origAcctIDs = new HashSet<>();  // Originator account ID set
	private Set<String> beneAcctIDs = new HashSet<>();  // Beneficiary account ID set
    private List<Account> origAccts = new ArrayList<>();  // Originator accounts from which this account receives money
    private List<Account> beneAccts = new ArrayList<>();  // Beneficiary accounts to which this account sends money
	private int numSARBene = 0;  // Number of SAR beneficiary accounts
	private String bankID = "";  // Bank ID
    
    private Account prevOrig = null;  // Previous originator account

	List<Alert> alerts = new ArrayList<>();
	List<AccountGroup> accountGroups = new ArrayList<>();

    private Map<String, String> tx_types = new HashMap<>();  // Receiver Client ID --> Transaction Type

	private static List<String> all_tx_types = new ArrayList<>();

	private ArrayList<String> paramFile = new ArrayList<>();

	private double balance = 0;

	protected long startStep = 0;
	protected long endStep = 0;

	private Random random;


	public Account() {
		this.id = "-";
	}

	/**
	 * Constructor of the account object
	 * @param id Account ID
     * @param interval Default transaction interval
	 * @param initBalance Initial account balance
	 * @param start Start step
	 * @param end End step
	 */
    public Account(String id, int interval, float initBalance, String bankID, Random rand) {
		this.id = id;
		this.setBalance(initBalance);
		this.bankID = bankID;
		this.random = rand;

		this.cashInModel = new CashInModel();
		this.cashInModel.setAccount(this);
		this.cashInModel.setParameters(interval, -1, -1);

		this.cashOutModel = new CashOutModel();
		this.cashOutModel.setAccount(this);
		this.cashOutModel.setParameters(interval, -1, -1);
	}

	public String getBankID() {
		return this.bankID;
	}

	public long getStartStep(){
		return this.startStep;
	}
	public long getEndStep(){
		return this.endStep;
	}

	void setSAR(boolean flag){
		this.isSAR = flag;
	}

	public boolean isSAR() {
		return this.isSAR;
	}

	public double getBalance() {
		return this.balance;
	}

	public void setBalance(double balance) {
		this.balance = balance;
	}

    public void withdraw(double ammount) {
        if (this.balance < ammount) {
            this.balance = 0;
        } else {
            this.balance -= ammount;
        }
    }

	public void deposit(double ammount){
		this.balance += ammount;
	}

	void setBranch(Branch branch) {
		this.branch = branch;
	}

	public Branch getBranch(){
		return this.branch;
	}

	public void addBeneAcct(Account bene){
		String beneID = bene.id;
		if(beneAcctIDs.contains(beneID)){  // Already added
			return;
		}

		if(ModelParameters.shouldAddEdge(this, bene)){
			beneAccts.add(bene);
			beneAcctIDs.add(beneID);

			bene.origAccts.add(this);
			bene.origAcctIDs.add(id);

			if(bene.isSAR){
				numSARBene++;
			}
		}
	}

	public void addTxType(Account bene, String ttype){
		this.tx_types.put(bene.id, ttype);
		all_tx_types.add(ttype);
	}

	public String getTxType(Account bene) {
		String destID = bene.id;

		if (this.tx_types.containsKey(destID)) {
			return tx_types.get(destID);
		} else if (!this.tx_types.isEmpty()) {
			List<String> values = new ArrayList<>(this.tx_types.values());
			return values.get(this.random.nextInt(values.size()));
		} else {
			return Account.all_tx_types.get(this.random.nextInt(Account.all_tx_types.size()));
		}
	}

	/**
	 * Get previous (originator) accounts
	 * @return Originator account list
	 */
	public List<Account> getOrigList(){
		return this.origAccts;
	}

	/**
	 * Get next (beneficiary) accounts
	 * @return Beneficiary account list
	 */
	public List<Account> getBeneList(){
		return this.beneAccts;
	}

	public void printBeneList(){
		System.out.println(this.beneAccts);
	}

	public int getNumSARBene(){
		return this.numSARBene;
	}

	public float getPropSARBene(){
		if(numSARBene == 0){
			return 0.0F;
		}
		return (float)numSARBene / beneAccts.size();
	}

	/**
	 * Register this account to the specified alert.
	 * @param alert Alert
	 */
	public void addAlert(Alert alert) {
		this.alerts.add(alert);
	}
    

	public void addAccountGroup(AccountGroup accountGroup) {
		this.accountGroups.add(accountGroup);
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
		
		for (Alert alert : this.alerts) {
			if (this == alert.getMainAccount()) {
				alert.registerTransactions(step, this);
			}
		}

		for (AccountGroup accountGroup : this.accountGroups) {
			Account account = accountGroup.getMainAccount();
			if (this == accountGroup.getMainAccount()) {
				accountGroup.registerTransactions(step, account);
			}
		}

		handleCashTransaction(amlsim);
	}

	/**
	 * Make cash transactions (deposit and withdrawal)
	 */
	private void handleCashTransaction(AMLSim amlsim){
		long step = amlsim.schedule.getSteps();
		this.cashInModel.makeTransaction(step);
		this.cashOutModel.makeTransaction(step);
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

	public ArrayList<String> getParamFile() {
		return paramFile;
	}

	public void setParamFile(ArrayList<String> paramFile) {
		this.paramFile = paramFile;
	}
}
