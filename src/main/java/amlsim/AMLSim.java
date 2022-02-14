package amlsim;

import amlsim.model.AbstractTransactionModel;
import amlsim.model.ModelParameters;
import amlsim.model.cash.CashInModel;
import amlsim.model.cash.CashOutModel;
import amlsim.model.normal.EmptyModel;
import amlsim.model.normal.FanInTransactionModel;
import amlsim.model.normal.FanOutTransactionModel;
import amlsim.model.normal.ForwardTransactionModel;
import amlsim.model.normal.MutualTransactionModel;
import amlsim.model.normal.PeriodicalTransactionModel;
import amlsim.model.normal.SingleTransactionModel;
import amlsim.model.aml.AMLTypology;
import amlsim.stat.Diameter;
import sim.engine.SimState;

import java.io.*;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.logging.*;

/**
 * AMLSimulator Main class
 */
public class AMLSim extends SimState {

    private static SimProperties simProp;
	private static final int TX_SIZE = 10000000;  // Transaction buffer size
	private static TransactionRepository txs = new TransactionRepository(TX_SIZE);
	private static Logger logger = Logger.getLogger("AMLSim");
//	private static int seed;
	private static Random rand;

	private Map<String, Integer> idMap = new HashMap<>();  // Account ID --> Index
	private Map<Long, Alert> alerts = new HashMap<>();  // Alert ID --> Alert (AML typology) object
	private Map<Long, AccountGroup> accountGroupsMap = new HashMap<>();
	private int numBranches = 0;
	private ArrayList<Branch> branches = new ArrayList<>();
	private int normalTxInterval = 30;  // Default transaction interval for normal accounts
//    private int sarTxInterval = 10;  // Default transaction interval for SAR accounts
//    private float sarBalanceRatio = 10.0F; // Multiplier of initial balance for SAR accounts

	private static String simulatorName = null;
	private ArrayList<String> paramFile = new ArrayList<>();
	private ArrayList<String> actions = new ArrayList<>();
	private ArrayList<Account> accounts = new ArrayList<Account>();
	private BufferedWriter bufWriter;
	private static long numOfSteps = 1;  // Number of simulation steps
	private static int currentLoop = 0;  // Simulation iteration counter
	private static String txLogFileName = "";

	private String accountFile = "";
	private String transactionFile = "";
	private String normalModelsFile = "";
	private String alertMemberFile = "";
	private String counterFile = "";
	private String diameterFile = "";

	private static Diameter diameter;
	private boolean computeDiameter = false;


	private AMLSim(long seed) {
		super(seed);
		AMLSim.rand = new Random(seed);
		Handler handler = new ConsoleHandler();
		logger.addHandler(handler);
		java.util.logging.Formatter formatter = new SimpleFormatter();
		handler.setFormatter(formatter);
        simulatorName = simProp.getSimName();
	}
 
	public static Random getRandom(){
	    return rand;
    }

	public static Logger getLogger(){
	    return logger;
    }

    public static SimProperties getSimProp(){
		return simProp;
	}

	public void setCurrentLoop(int currentLoop){
		AMLSim.currentLoop = currentLoop;
	}

	private List<Account> getAccounts() {
		return this.accounts;
	}
    
    /**
     * Get the number of simulation steps
     * @return Simulation steps as long
     */
	public static long getNumOfSteps(){
		return numOfSteps;
	}
    
    /**
     * Get an account object from an account ID
     * @param id Account ID
     * @return Account object
     */
    private Account getAccountFromID(String id){
		int index = this.idMap.get(id);
		return (Account) this.getAccounts().get(index);
	}
    
    /**
     * Initialize AMLSim by loading account and transaction list files
     */
	public void initSimulation() {
		try {
			loadAccountFile(this.accountFile);
		} catch (IOException e) {
			System.err.println("Cannot load account file: " + this.accountFile);
			e.printStackTrace();
			System.exit(1);
		}

		try {
			loadTransactionFile(this.transactionFile);
		} catch (IOException e) {
			System.err.println("Cannot load transaction file: " + this.transactionFile);
			e.printStackTrace();
			System.exit(1);
		}

		try {
			loadNormalModelsFile(this.normalModelsFile);
		} catch (IOException e) {
			System.err.println("Cannot load normal model file: " + this.normalModelsFile);
			e.printStackTrace();
			System.exit(1);
		}

		try {
			loadAlertMemberFile(this.alertMemberFile);
		} catch (IOException e) {
			System.err.println("Cannot load alert file: " + this.alertMemberFile);
			e.printStackTrace();
			System.exit(1);
		}
	}

	public void loadParametersFromFile() {
		numOfSteps = simProp.getSteps();
		// Default transaction interval for accounts
		this.normalTxInterval = simProp.getNormalTransactionInterval();

		// Number of transactions for logging buffer
        int transactionLimit = simProp.getTransactionLimit();
        if(transactionLimit > 0){  // Set the limit only if the parameter is positive value
            txs.setLimit(transactionLimit);
        }

		// Parameters of Cash Transactions
		int norm_in_int = simProp.getCashTxInterval(true, false);  // Interval of cash-in transactions for normal account
		int suspicious_in_int = simProp.getCashTxInterval(true, true);  // Interval of cash-in transactions for suspicious account
		float norm_in_min = simProp.getCashTxMinAmount(true, false);  // Minimum amount of cash-in transactions for normal account
		float norm_in_max = simProp.getCashTxMaxAmount(true, false);  // Maximum amount of cash-in transactions for normal account
		float suspicious_in_min = simProp.getCashTxMinAmount(true, true);  // Minimum amount of cash-in transactions for suspicious account
		float suspicious_in_max = simProp.getCashTxMaxAmount(true, true);  // Maximum amount of cash-in transactions for suspicious account
		CashInModel.setParam(norm_in_int, suspicious_in_int, norm_in_min, norm_in_max, suspicious_in_min, suspicious_in_max);

		int norm_out_int = simProp.getCashTxInterval(false, false);  // Interval of cash-out transactions for normal account
		int suspicious_out_int = simProp.getCashTxInterval(false, true);  // Interval of cash-out transactions for suspicious account
		float norm_out_min = simProp.getCashTxMinAmount(false, false);  // Minimum amount of cash-out transactions for normal account
		float norm_out_max = simProp.getCashTxMaxAmount(false, false);  // Maximum amount of cash-out transactions for normal account
		float suspicious_out_min = simProp.getCashTxMinAmount(false, true);  // Minimum amount of cash-out transactions for suspicious account
		float suspicious_out_max = simProp.getCashTxMaxAmount(false, true);  // Maximum amount of cash-out transactions for suspicious account
		CashOutModel.setParam(norm_out_int, suspicious_out_int, norm_out_min, norm_out_max, suspicious_out_min, suspicious_out_max);


		// Create branches (for cash transactions)
		this.numBranches = simProp.getNumBranches();
		if(this.numBranches <= 0){
			throw new IllegalStateException("The numBranches must be positive");
		}
		for(int i=0; i<this.numBranches; i++) {
			this.branches.add(new Branch(i));
		}

        this.accountFile = simProp.getInputAcctFile();
        this.transactionFile = simProp.getInputTxFile();
		this.normalModelsFile = simProp.getNormalModelsFile();
        this.alertMemberFile = simProp.getInputAlertMemberFile();
        this.counterFile = simProp.getCounterLogFile();
        this.diameterFile = simProp.getDiameterLogFile();
        this.computeDiameter = simProp.isComputeDiameter();

        if(computeDiameter && diameterFile != null){
            try{
                BufferedWriter writer = new BufferedWriter(new FileWriter(diameterFile));
                writer.close();
            }catch (IOException e){
                e.printStackTrace();
                computeDiameter = false;
            }
            if(computeDiameter){
                logger.info("Compute transaction graph diameters and write them to: " + diameterFile);
            }else{
                logger.info("Transaction graph diameter computation is disabled");
            }
        }
	}


	private static Map<String, Integer> getColumnIndices(String header){
		Map<String, Integer> columnIndex = new HashMap<>();
		String[] element= header.split(",");
		for(int i=0; i<element.length; i++){
			columnIndex.put(element[i], i);
		}
		return columnIndex;
	}
	

	private void loadAccountFile(String accountFile) throws IOException{
		BufferedReader reader = new BufferedReader(new FileReader(accountFile));
		String line = reader.readLine();
		logger.info("Account CSV header: " + line);
		Map<String, Integer> columnIndex = getColumnIndices(line);

		while((line = reader.readLine()) != null){
			String[] elements = line.split(",");
            String accountID = elements[columnIndex.get("ACCOUNT_ID")];
			boolean isSAR = elements[columnIndex.get("IS_SAR")].toLowerCase().equals("true");
			float initBalance = Float.parseFloat(elements[columnIndex.get("INIT_BALANCE")]);
			String bankID = elements[columnIndex.get("BANK_ID")];


			Account account;
			if (isSAR) {
				account = new SARAccount(accountID, normalTxInterval, initBalance, bankID,
						getRandom());
			} else {
				account = new Account(accountID, normalTxInterval, initBalance, bankID,
						getRandom());
			}

			int index = this.getAccounts().size();
			account.setBranch(this.branches.get(index % this.numBranches));
			this.getAccounts().add(account);
			this.idMap.put(accountID, index);
			this.schedule.scheduleRepeating(account);
		}
		int numAccounts = idMap.size();
		logger.info("Number of total accounts: " + numAccounts);
		diameter = new Diameter(numAccounts);

		reader.close();
	}

	private void loadTransactionFile(String transactionFile) throws IOException{
		BufferedReader reader = new BufferedReader(new FileReader(transactionFile));
		String line = reader.readLine();
		Map<String, Integer> columnIndex = getColumnIndices(line);
		while((line = reader.readLine()) != null){
			String[] elements = line.split(",");
            String srcID = elements[columnIndex.get("src")];
            String dstID = elements[columnIndex.get("dst")];

            String ttype = elements[columnIndex.get("ttype")];

			Account src = getAccountFromID(srcID);
			Account dst = getAccountFromID(dstID);
			src.addBeneAcct(dst);
			src.addTxType(dst, ttype);
		}
		reader.close();
	}

	private void loadNormalModelsFile(String filename) throws IOException {
		try (BufferedReader reader = new BufferedReader(new FileReader(filename))) {
			String line;
			line = reader.readLine();
			Map<String, Integer> columnIndexMap = getColumnIndices(line);

			while((line = reader.readLine()) != null) {
				String[] elements = line.split(",");

				String type = elements[columnIndexMap.get("type")];
				String accountID = elements[columnIndexMap.get("accountID")];
				long accountGroupId = Long.parseLong(elements[columnIndexMap.get("modelID")]);
				boolean isMain = elements[columnIndexMap.get("isMain")].toLowerCase().equals("true");
				

				AccountGroup accountGroup;
				if (this.accountGroupsMap.containsKey(accountGroupId)) {
					accountGroup = this.accountGroupsMap.get(accountGroupId);
				}
				else {
					accountGroup = new AccountGroup(accountGroupId, this);
					accountGroupsMap.put(accountGroupId, accountGroup);
				}

				Account account = getAccountFromID(accountID);
				
				accountGroup.addMember(account);
				if (isMain) {
					accountGroup.setMainAccount(account);
				}

				account.addAccountGroup(accountGroup);

				AbstractTransactionModel model;

				switch (type) {
					case AbstractTransactionModel.SINGLE: model = new SingleTransactionModel(accountGroup, rand); break;
					case AbstractTransactionModel.FAN_OUT: model= new FanOutTransactionModel(accountGroup, rand); break;
					case AbstractTransactionModel.FAN_IN: model = new FanInTransactionModel(accountGroup, rand); break;
					case AbstractTransactionModel.MUTUAL: model = new MutualTransactionModel(accountGroup, rand); break;
					case AbstractTransactionModel.FORWARD: model = new ForwardTransactionModel(accountGroup, rand); break;
					case AbstractTransactionModel.PERIODICAL: model = new PeriodicalTransactionModel(accountGroup, rand); break;
					default: System.err.println("Unknown model type: " + type); model = new EmptyModel(accountGroup, rand); break;
				}

				accountGroup.setModel(model);

				model.setParameters(this.normalTxInterval, -1, -1);
			}
		}
	}


	private void loadAlertMemberFile(String alertFile) throws IOException{
		logger.info("Load alert member list from:" + alertFile);

		BufferedReader reader = new BufferedReader(new FileReader(alertFile));
		String line = reader.readLine();
		Map<String, Integer> columnIndex = getColumnIndices(line);
		Map<Long, Integer> scheduleModels = new HashMap<>();
		while((line = reader.readLine()) != null){
			String[] elements = line.split(",");
			long alertID = Long.parseLong(elements[columnIndex.get("alertID")]);
            String accountID = elements[columnIndex.get("accountID")];
			boolean isMain = elements[columnIndex.get("isMain")].toLowerCase().equals("true");
			boolean isSAR = elements[columnIndex.get("isSAR")].toLowerCase().equals("true");
			int modelID = Integer.parseInt(elements[columnIndex.get("modelID")]);
			double minAmount = Double.parseDouble(elements[columnIndex.get("minAmount")]);
		    double maxAmount = Double.parseDouble(elements[columnIndex.get("maxAmount")]);
			int startStep = Integer.parseInt(elements[columnIndex.get("startStep")]);
			int endStep = Integer.parseInt(elements[columnIndex.get("endStep")]);
			int scheduleID = Integer.parseInt(elements[columnIndex.get("scheduleID")]);

			if(minAmount > maxAmount){
				throw new IllegalArgumentException(String.format("minAmount %f is larger than maxAmount %f", minAmount, maxAmount));
			}
			if(startStep > endStep){
				throw new IllegalArgumentException(String.format("startStep %d is larger than endStep %d", startStep, endStep));
			}

			Alert alert;
			if(alerts.containsKey(alertID)){  // Get an AML typology object and update the minimum/maximum amount
				alert = alerts.get(alertID);
				AMLTypology model = alert.getModel();
				model.updateMinAmount(minAmount);
				model.updateMaxAmount(maxAmount);
				model.updateStartStep(startStep);
				model.updateEndStep(endStep);

			}else{  // Create a new AML typology object
				AMLTypology model = AMLTypology.createTypology(modelID, minAmount, maxAmount, startStep, endStep);
				alert = new Alert(alertID, model, this);
				alerts.put(alertID, alert);
			}
			Account account = getAccountFromID(accountID);
			alert.addMember(account);
			if(isMain){
				alert.setMainAccount(account);
			}
			account.setSAR(isSAR);
			scheduleModels.put(alertID, scheduleID);
		}
		for(long alertID : scheduleModels.keySet()){
			int modelID = scheduleModels.get(alertID);
			alerts.get(alertID).getModel().setParameters(modelID);
		}
		reader.close();
	}

	/**
	 * Define the simulator name and an output log directory.
	 * If the simulator name is not specified, generate it using the current time.
	 */
	private void initSimulatorName() {
		if(AMLSim.simulatorName == null) {  // Not specified in the args
			Calendar c = Calendar.getInstance();
			SimpleDateFormat format = new SimpleDateFormat("yyyyMMdd_HHmmss_SSS");
			AMLSim.simulatorName = "PS_" + format.format(c.getTime());
		}
		logger.info("Simulator Name: " + AMLSim.simulatorName);

        String dirPath = simProp.getOutputDir();
		File f = new File(dirPath);
		if(f.exists()){
            logger.warning("Output log directory already exists: " + dirPath);
        }else {
            boolean result = f.mkdir();
            if (!result) {
                throw new IllegalStateException("Output log directory cannot be created to: " + dirPath);
            }
        }
	}


	private void initTxLogBufWriter(String logFileName) {
		try {
			FileWriter writer = new FileWriter(new File(logFileName));
			this.bufWriter = new BufferedWriter(writer);
			this.bufWriter.write("step,type,amount,nameOrig,oldbalanceOrig,newbalanceOrig,nameDest,oldbalanceDest,newbalanceDest,isSAR,alertID\n");
			this.bufWriter.close();
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	static String getTxLogFileName(){
		return txLogFileName;
	}

	public void executeSimulation(){
		//Load the parameters from the .property file
		loadParametersFromFile();

		// increase transfer limit with the current loop
		initSimulatorName();

		//Initiate the dumpfile output writer
        txLogFileName = simProp.getOutputTxLogFile();
		initTxLogBufWriter(txLogFileName);
		logger.info("Transaction log file: " + txLogFileName);

		// Create account objects
		super.start();
		this.initSimulation();

		// Starting the simulation
		long begin = System.currentTimeMillis();
		System.out.println("Starting AMLSim Running for " + numOfSteps + " steps. Current loop:" + AMLSim.currentLoop);

		long step;
		while ((step = super.schedule.getSteps()) < numOfSteps) {
			if (!super.schedule.step(this))
				break;
			if (step % 100 == 0 && step != 0) {
				long tm = System.currentTimeMillis();
				System.out.println("Time Step " + step + ", " + (tm - begin)/1000 + " [s]");
			}
			else {
				System.out.print("*");
			}
			if (computeDiameter && step % 10 == 0 && step > 0){
				double[] result = diameter.computeDiameter();
				writeDiameter(step, result);
			}
		}
		txs.flushLog();
		txs.writeCounterLog(numOfSteps, counterFile);
		System.out.println(" - Finished running " + step + " steps ");

		//Finishing the simulation
		super.finish();
		long end = System.currentTimeMillis();

		double total = end - begin;
		total = total/1000;  // ms --> s
		System.out.println("\nIt took: " + total + " seconds to execute the simulation\n");
		System.out.println("Simulation name: " + AMLSim.simulatorName);
	}
    
    /**
     * Manage a transaction for logging and diameter computation of the whole transaction network
     * @param step Simulation step
     * @param desc Transaction description (e.g. type)
     * @param amt Amount
     * @param orig Originator account
     * @param bene Beneficiary account
     * @param isSAR SAR flag
     * @param alertID Alert ID
     */
	public static void handleTransaction(long step, String desc, double amt, Account orig, Account bene,
										 boolean isSAR, long alertID){
        // Reduce the balance of the originator account
        String origID = orig.getID();
		float origBefore = (float)orig.getBalance();
		orig.withdraw(amt);
		float origAfter = (float)orig.getBalance();
		
		// Increase the balance of the beneficiary account
        String beneID = bene.getID();
        float beneBefore = (float)bene.getBalance();
		bene.deposit(amt);
		float beneAfter = (float)bene.getBalance();

		txs.addTransaction(step, desc, amt, origID, beneID, origBefore, origAfter, beneBefore, beneAfter, isSAR, alertID);
		diameter.addEdge(origID, beneID);
	}
    
    /**
     * Write diameters of the transaction network snapshots to a CSV file
     * @param step Simulation step
     * @param result Diameter and radius of the transaction network as double array
     */
	private void writeDiameter(long step, double[] result){
		try{
			BufferedWriter writer = new BufferedWriter(new FileWriter(diameterFile, true));
			writer.write(step + "," + result[0] + "," + result[1] + "\n");
			writer.close();
		}catch (IOException e){
			e.printStackTrace();
		}
	}


	public static void main(String[] args){
        if(args.length < 1){
            System.err.println("Usage: java amlsim.AMLSim [ConfFile]");
            System.exit(1);
        }

		// Loading configuration JSON file instead of parsing command line arguments
        String confFile = args[0];
        try {
            simProp = new SimProperties(confFile);
        }catch (IOException e){
            System.err.println("Cannot load configuration JSON file: " + confFile);
            e.printStackTrace();
            System.exit(1);
        }

        if(args.length >= 2){  // Load transaction model parameter file (optional)
        	String propFile = args[1];
			ModelParameters.loadProperties(propFile);
		}

        int seed = simProp.getSeed();
        AMLSim sim = new AMLSim(seed);
        sim.setCurrentLoop(0);
        sim.executeSimulation();
	}
}

