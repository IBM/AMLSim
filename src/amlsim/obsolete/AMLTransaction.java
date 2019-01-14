package amlsim.obsolete;

import amlsim.Account;
import paysim.ClientBeta;
import paysim.Merchant;
import paysim.Transaction;

/**
 * @deprecated This class is obsolete because of performance overheads
 */
public class AMLTransaction extends Transaction {
	/**
	 * Description of a transaction
	 */
	private static final long serialVersionUID = 1L;
	private Account clientOrigBefore = new Account();
	private Account clientOrigAfter = new Account();
	private Account clientDestBefore = new Account();
	private Account clientDestAfter = new Account();
	private long alertID = -1;

	public long getAlertID(){
		return alertID;
	}

	public void setAlertID(long alertID){
		this.alertID = alertID;
	}

	private ClientBeta clientBetaOrigBefore = new ClientBeta();
	

	private ClientBeta clientBetaOrigAfter = new ClientBeta();
	private ClientBeta clientBetaDestBefore = new ClientBeta();
	private ClientBeta clientBetaDestAfter = new ClientBeta();

	private Merchant merchantAfter = new Merchant();
	private int fraudster = 0;
	private double newBalanceDest = 0;
	private double newBalanceOrig = 0;
	long step;
	String profileOrig, profileDest;
	private int day = 0;
	private int hour = 0;

	public long getStep() {
		return step;
	}

	public void setStep(long step) {
		this.step = step;
	}

	public AMLTransaction() {
		this.setType((short)0);
		this.setAmount(0);
		this.newBalanceDest = 0;
		this.newBalanceOrig = 0;
	}

	//The constructor used in my agent
	public AMLTransaction(Long step, Account clientOrig, short type, double amount,
						  String description) {
		super();
		this.step = step;
		this.clientOrigBefore.setClient(clientOrig);;
		this.newBalanceOrig = clientOrig.getBalance();
		this.setType(type);
		this.setAmount((long)amount);
		this.setDescription(description);
	}
	
	//Used for transfer
	public AMLTransaction(Long step, Account clientOriginalBefore, Account clientOrigAfter, short type, double amount,
						  String description) {
		super();
		this.step = step;
		this.clientOrigBefore.setClient(clientOriginalBefore);
		this.clientOrigAfter.setClient(clientOrigAfter);
		
		this.newBalanceOrig = this.clientOrigBefore.getBalance();
		this.newBalanceDest = clientOrigAfter.getBalance();

		this.setType(type);
		this.setAmount((long)amount);
		this.setDescription(description);
	}
	
	public AMLTransaction(Long step, ClientBeta clientOriginalBefore, ClientBeta clientOrigAfter, short type, double amount,
			String description) {
		super();
		this.step = step;
		this.clientBetaOrigBefore.setClientBeta(clientOriginalBefore);
		this.clientBetaOrigAfter.setClientBeta(clientOrigAfter);
		
		this.newBalanceOrig = this.clientOrigBefore.getBalance();
		this.newBalanceDest = clientOrigAfter.getBalance();

		this.setType(type);
		this.setAmount((long)amount);
		this.setDescription(description);
	}

	public AMLTransaction(Long step, ClientBeta clientOrig, short type, double amount,
			String description) {
		super();
		this.step = step;
		this.clientBetaOrigBefore.setClientBeta(clientOrig);;
		this.newBalanceOrig = clientOrig.getBalance();
		this.setType(type);
		this.setAmount((long)amount);
		this.setDescription(description);
	}

	public Account getClientOrigBefore() {
		return clientOrigBefore;
	}

	public void setClientOrigBefore(Account clientOrigBefore) {
		this.clientOrigBefore = clientOrigBefore;
	}

	public Account getClientOrigAfter() {
		return clientOrigAfter;
	}

	public void setClientOrigAfter(Account clientOrigAfter) {
		this.clientOrigAfter = clientOrigAfter;
	}

	public Account getClientDestBefore() {
		return clientDestBefore;
	}

	public void setClientDestBefore(Account clientDestBefore) {
		this.clientDestBefore = clientDestBefore;
	}

	public Account getClientDestAfter() {
		return clientDestAfter;
	}

	public void setClientDestAfter(Account clientDestAfter) {
		this.clientDestAfter = clientDestAfter;
	}

	public ClientBeta getClientBetaOrigBefore() {
		return clientBetaOrigBefore;
	}

	public void setClientBetaOrigBefore(ClientBeta clientBetaOrigBefore) {
		this.clientBetaOrigBefore = clientBetaOrigBefore;
	}

	public ClientBeta getClientBetaOrigAfter() {
		return clientBetaOrigAfter;
	}

	public void setClientBetaOrigAfter(ClientBeta clientBetaOrigAfter) {
		this.clientBetaOrigAfter = clientBetaOrigAfter;
	}

	public ClientBeta getClientBetaDestBefore() {
		return clientBetaDestBefore;
	}

	public void setClientBetaDestBefore(ClientBeta clientBetaDestBefore) {
		this.clientBetaDestBefore = clientBetaDestBefore;
	}

	public ClientBeta getClientBetaDestAfter() {
		return clientBetaDestAfter;
	}

	public void setClientBetaDestAfter(ClientBeta clientBetaDestAfter) {
		this.clientBetaDestAfter = clientBetaDestAfter;
	}
}
