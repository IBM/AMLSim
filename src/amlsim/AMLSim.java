package amlsim;

import amlsim.model.cash.CashInModel;
import amlsim.model.cash.CashOutModel;
import amlsim.model.aml.AMLTypology;
import amlsim.stat.Diameter;
import paysim.*;

import java.io.*;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.logging.*;

/**
 * AMLSimulator Main class
 */
public class AMLSim extends ParameterizedPaySim {

    private static SimProperties simProp;
	public static final boolean TX_OPT = true;  // Optimized transaction
	private static final int TX_SIZE = 10000000;  // Transaction buffer size
	private static TransactionRepository txs = new TransactionRepository(TX_SIZE);
	private static Logger logger = Logger.getLogger("AMLSim");

	private Map<String, Integer> idMap = new HashMap<>();  // Account ID --> Index
	private Map<Long, Alert> alertGroups = new HashMap<>();
	private int numBranches = 0;
	private ArrayList<Branch> branches = new ArrayList<>();
	private int defaultTxInterval = 30;  // Default transaction interval for accounts

	private static String simulatorName = null;
	private ArrayList<String> paramFile = new ArrayList<>();
	private ArrayList<String> actions = new ArrayList<>();
	private BufferedWriter bufWriter;
	private static long numOfSteps = 1;  // Number of simulation steps
	private static int currentLoop = 0;  // Simulation iteration counter
	private static String txLogFileName = "";

	private String accountFile = "";
	private String transactionFile = "";
	private String alertMemberFile = "";
	private String counterFile = "";
	private String diameterFile = "";

	private static Diameter diameter;
	private boolean computeDiameter = false;


	private AMLSim(long seed) {
		super(seed);
		super.setTagName("1");
		Handler handler = new ConsoleHandler();
		logger.addHandler(handler);
		java.util.logging.Formatter formatter = new SimpleFormatter();
		handler.setFormatter(formatter);
        simulatorName = simProp.getSimName();
	}

	public static Logger getLogger(){
	    return logger;
    }

	public void setCurrentLoop(int currentLoop){
		AMLSim.currentLoop = currentLoop;
	}
	
	//Parse the arguments
	public void parseArgs(String[] args){
	    String paysimPropFile = "paramFiles/paysim.properties";  // TODO: to be removed with the PaySim dependency
        super.setPropertiesFile(paysimPropFile);
        logger.info("PaySim Properties File: " + paysimPropFile);

        numOfSteps = simProp.getSteps();
        logger.info("Simulation Steps: " + numOfSteps);
	}

	public void runSimulation(String[] args){
		parseArgs(args);
		executeSimulation();
	}

	public static long getNumOfSteps(){
		return numOfSteps;
	}

    private Account getClientFromID(String id){
		int index = this.idMap.get(id);
		return (Account) this.getClients().get(index);
	}

	public void initSimulation(){
		// Load account file
		try{
			loadAccountFile(this.accountFile);
		}catch(IOException e){
			System.err.println("Cannot load account file: " + this.accountFile);
			e.printStackTrace();
			System.exit(1);
		}

		// Load transaction file
		try{
			loadTransactionFile(this.transactionFile);
		}catch(IOException e){
			System.err.println("Cannot load transaction file: " + this.transactionFile);
			e.printStackTrace();
			System.exit(1);
		}

		// Load alert member file
		try{
			loadAlertMemberFile(this.alertMemberFile);
		}catch(IOException e){
			System.err.println("Cannot load alert file: " + this.alertMemberFile);
			e.printStackTrace();
			System.exit(1);
		}

		super.initSimulation();
	}

	public void loadParametersFromFile(){
		super.loadParametersFromFile();

        // Default transaction interval for accounts
        this.defaultTxInterval = simProp.getTransactionInterval();

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

	private final Set<String> baseColumns = new HashSet<>(Arrays.asList("ACCOUNT_ID", "IS_SAR", "TX_BEHAVIOR_ID", "INIT_BALANCE", "START_DATE", "END_DATE"));

	private void loadAccountFile(String accountFile) throws IOException{
		BufferedReader reader = new BufferedReader(new FileReader(accountFile));
		String line = reader.readLine();
		logger.info("Account CSV header: " + line);
		Map<String, Integer> columnIndex = getColumnIndices(line);
		Set<String> extraColumns = new HashSet<>(columnIndex.keySet());
		extraColumns.removeAll(baseColumns);

		while((line = reader.readLine()) != null){
			String[] elements = line.split(",");
            String accountID = elements[columnIndex.get("ACCOUNT_ID")];
			boolean isSAR = elements[columnIndex.get("IS_SAR")].toLowerCase().equals("true");
			int modelID = Integer.parseInt(elements[columnIndex.get("TX_BEHAVIOR_ID")]);
			float initBalance = Float.parseFloat(elements[columnIndex.get("INIT_BALANCE")]);
			int start = Integer.parseInt(elements[columnIndex.get("START_DATE")]);
			int end = Integer.parseInt(elements[columnIndex.get("END_DATE")]);
			int bankID = Integer.parseInt(elements[columnIndex.get("BANK_ID")]);

			Map<String, String> extraValues = new HashMap<>();
			for(String column : extraColumns){
			    int idx = columnIndex.get(column);
                extraValues.put(column, elements[idx]);
            }

			Account account = isSAR ? new SARAccount(accountID, modelID, defaultTxInterval, initBalance, start, end, bankID, extraValues)
					: new Account(accountID, modelID, defaultTxInterval, initBalance, start, end, bankID, extraValues);

			int index = this.getClients().size();
			account.setBranch(this.branches.get(index % this.numBranches));
			this.getClients().add(account);
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

			Account src = getClientFromID(srcID);
			Account dst = getClientFromID(dstID);
			src.addDest(dst);
			src.addTxType(dst, ttype);
		}
		reader.close();
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
            String clientID = elements[columnIndex.get("clientID")];

			boolean isSAR = elements[columnIndex.get("isSAR")].toLowerCase().equals("true");
			int modelID = Integer.parseInt(elements[columnIndex.get("modelID")]);
			float minAmount = Float.parseFloat(elements[columnIndex.get("minAmount")]);
			float maxAmount = Float.parseFloat(elements[columnIndex.get("maxAmount")]);
			int minStep = Integer.parseInt(elements[columnIndex.get("startStep")]);
			int maxStep = Integer.parseInt(elements[columnIndex.get("endStep")]);
			int scheduleID = Integer.parseInt(elements[columnIndex.get("scheduleID")]);

			if(minAmount > maxAmount){
				throw new IllegalArgumentException(String.format("minAmount %f is larger than maxAmount %f", minAmount, maxAmount));
			}
			if(minStep > maxStep){
				throw new IllegalArgumentException(String.format("startStep %d is larger than endStep %d", minStep, maxStep));
			}

			Alert alert;
			if(alertGroups.containsKey(alertID)){  // Get an AML typology object and update the minimum/maximum amount
				alert = alertGroups.get(alertID);
				AMLTypology model = alert.getModel();
				model.updateMinAmount(minAmount);
				model.updateMaxAmount(maxAmount);

			}else{  // Create a new AML typology object
				AMLTypology model = AMLTypology.createTypology(modelID, minAmount, maxAmount, minStep, maxStep);
				alert = new Alert(alertID, model, this);
				alertGroups.put(alertID, alert);
			}
			Account account = getClientFromID(clientID);
			alert.addMember(account);
			if(isSAR){
				alert.setMainAccount((SARAccount) account);
				account.setSAR(true);
			}
			scheduleModels.put(alertID, scheduleID);
		}
		for(long alertID : scheduleModels.keySet()){
			int modelID = scheduleModels.get(alertID);
			alertGroups.get(alertID).getModel().setParameters(modelID);
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

	private void loadAggregatedFile() {
		this.paramFile = new ArrayList<>();

		// TODO: Load actions (transaction types) from the parameter file
        this.actions.add("TRANSFER");
//		this.actions.add("CASH_IN");
//		this.actions.add("CASH_OUT");
//		this.actions.add("DEBIT");
//		this.actions.add("DEPOSIT");
//		this.actions.add("PAYMENT");
//		this.actions.add("TRANSFER");
	}


	private void initTxLogBufWriter(String logFileName) {
		try {
			FileWriter writer = new FileWriter(new File(logFileName));
			this.bufWriter = new BufferedWriter(writer);
			this.bufWriter.write("step,type,amount,nameOrig,oldbalanceOrg,newbalanceOrig,nameDest,oldbalanceDest,newbalanceDest,isSAR,alertID\n");
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
		loadAggregatedFile();

		//Initiate the dumpfile output writer
        txLogFileName = simProp.getOutputTxLogFile();
		initTxLogBufWriter(txLogFileName);
		logger.info("Transaction log file: " + txLogFileName);

		//add the param list to the object
		setParamFileList(this.paramFile);

		//Set all of the possible actions that can be done
		setActionTypes(this.actions);

		//Add the writer to the simulator
		setWriter(this.bufWriter);

		// Set total simulation steps
		setNrOfSteps(numOfSteps);

		// Create account objects
		super.start();

		// Starting the simulation
		long begin = System.currentTimeMillis();
		System.out.println("Starting PaySim Running for " + numOfSteps + " steps. Current loop:" + AMLSim.currentLoop);

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

	public static void handleTransaction(long step, String desc, float amt, Account orig, Account bene,
										 boolean isSAR, long alertID){
        String origID = orig.getID();

		float origBefore = (float)orig.getBalance();
		orig.withdraw(amt);
		float origAfter = (float)orig.getBalance();

        String beneID = bene.getID();

		float beneBefore = (float)bene.getBalance();
		bene.deposit(amt);
		float beneAfter = (float)bene.getBalance();

		txs.addTransaction(step, desc, amt, origID, beneID, origBefore, origAfter, beneBefore, beneAfter, isSAR, alertID);
		diameter.addEdge(origID, beneID);
	}

	private void writeDiameter(long step, double[] result){
		try{
			BufferedWriter writer = new BufferedWriter(new FileWriter(diameterFile, true));
			writer.write(step + "," + result[0] + "," + result[1] + "\n");
			writer.close();
		}catch (IOException e){
			e.printStackTrace();
		}
	}


	public void writeLog() {
        // Use transaction repository instead of transaction object list
	}

	public void writeSummaryFile() {
		// Skip writing summary file of PaySim
	}


	public static void main(String[] args){
        if(args.length < 1){
            System.err.println("Usage: java amlsim.AMLSim [ConfFile]");
            System.exit(1);
        }

		// Loading configuration JSON file instead of parsing command line arguments
        String propFile = args[0];
        try {
            simProp = new SimProperties(propFile);
        }catch (IOException e){
            System.err.println("Cannot load configuration JSON file: " + propFile);
            e.printStackTrace();
            System.exit(1);
        }

        int seed = simProp.getSeed();
        AMLSim sim = new AMLSim(seed);
        sim.setCurrentLoop(0);
        sim.runSimulation(args);
	}
}

