package amlsim;

import amlsim.model.cash.CashInModel;
import amlsim.model.cash.CashOutModel;
import amlsim.model.fraud.FraudTransactionModel;
import amlsim.stat.Diameter;
import paysim.*;

import java.io.*;
import java.math.BigDecimal;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.logging.*;

/**
 * AMLSimulator Main class
 */
public class AMLSim extends ParameterizedPaySim {

	public static final boolean TX_OPT = true;  // Optimized transaction
	public static final int TX_SIZE = 10000000;  // Transaction buffer size
	private static TransactionRepository txs = new TransactionRepository(TX_SIZE);
	private static Logger logger = Logger.getLogger("AMLSim");
	private Handler handler = new ConsoleHandler();
	private java.util.logging.Formatter formatter = new SimpleFormatter();

//	private Map<Long, Integer> idMap = new HashMap<>();  // Account ID --> Index
    private Map<String, Integer> idMap = new HashMap<>();  // Account ID --> Index
	private Map<Long, Alert> alertGroups = new HashMap<>();
	private int numBranches = 0;
	private ArrayList<Branch> branches = new ArrayList<>();
	private int defaultInterval = 30;  // Default transaction interval for accounts

	private static String simulatorName = null;
	private ArrayList<String> paramFile = new ArrayList<>();
	private ArrayList<String> actions = new ArrayList<>();
	private BufferedWriter bufWriter;
	private static long numOfSteps = 1;  // Number of simulation steps
	private int numOfRepeat = 0;    // Number of simulation iterations
	private static int currentLoop = 0;  // Simulation iteration counter
	public static String txLogFileName = "";

	private String accountFile = "";
	private String transactionFile = "";
	private String alertFile = "";
	private String counterFile = "";
	private String diameterFile = "";

	private static Diameter diameter;
	private boolean computeDiameter = false;


	private AMLSim(long seed) {
		super(seed);
		super.setTagName("1");
        logger.addHandler(handler);
        handler.setFormatter(formatter);
	}

	public static Logger getLogger(){
	    return logger;
    }

	public void setCurrentLoop(int currentLoop){
		AMLSim.currentLoop = currentLoop;
	}
	
	//Parse the arguments
	public void parseArgs(String[] args){
		//Parse the arguments given
		for (int x = 0; x < args.length - 1; x++){
			switch (args[x]) {
				case "-file":
					String filePath = args[x + 1];
					super.setPropertiesFile(filePath);
					logger.info("Properties File: " + filePath);
					break;
				case "-for":  //Gets the number of steps
					numOfSteps = Long.parseLong(args[x + 1]);
					this.setNrOfSteps(numOfSteps);
                    logger.info("Simulation Steps: " + numOfSteps);
					break;
				case "-r":  //Gets the number of repetitions
					numOfRepeat = Integer.parseInt(args[x + 1]);
                    logger.info("Simulation Repeats: " + numOfRepeat);
					break;
				case "-inc":  //Gets the number of incrementations for each repetition
					double incRepeat = Double.parseDouble(args[x + 1]);
					break;
				case "-name":  // Simulation name (optional)
					simulatorName = args[x + 1];
                    logger.info("Simulator Name: " + simulatorName);
					break;
			}
		}
	}
	
	public void runSimulation(String[] args){
		parseArgs(args);
		numOfRepeat = 1;
		executeSimulation();
	}

	public static long getNumOfSteps(){
		return numOfSteps;
	}

    public Account getClientFromID(String id){
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

		// Load alert file
		try{
			loadAlertFile(this.alertFile);
		}catch(IOException e){
			System.err.println("Cannot load fraud file: " + this.alertFile);
			e.printStackTrace();
			System.exit(1);
		}

		super.initSimulation();
	}

	public void loadParametersFromFile(){
		super.loadParametersFromFile();
        Properties prop = this.getParamters();

        // Default transaction interval for accounts
        this.defaultInterval = Integer.parseInt(prop.getProperty("transactionInterval"));

		// Number of transaction limit
        int transactionLimit = Integer.parseInt(prop.getProperty("transactionLimit"));
        if(transactionLimit > 0){
            txs.setLimit(transactionLimit);
        }

		// Parameters of Cash Transactions
		int norm_in_int = Integer.parseInt(prop.getProperty("normal_cash_in_interval"));  // Interval of cash-in transactions for normal account
		int fraud_in_int = Integer.parseInt(prop.getProperty("fraud_cash_in_interval"));  // Interval of cash-in transactions for suspicious account
		float norm_in_min = Float.parseFloat(prop.getProperty("normal_cash_in_min"));  // Minimum amount of cash-in transactions for normal account
		float norm_in_max = Float.parseFloat(prop.getProperty("normal_cash_in_max"));  // Maximum amount of cash-in transactions for normal account
		float fraud_in_min = Float.parseFloat(prop.getProperty("fraud_cash_in_min"));  // Minimum amount of cash-in transactions for suspicious account
		float fraud_in_max = Float.parseFloat(prop.getProperty("fraud_cash_in_max"));  // Maximum amount of cash-in transactions for suspicious account
		CashInModel.setParam(norm_in_int, fraud_in_int, norm_in_min, norm_in_max, fraud_in_min, fraud_in_max);

		int norm_out_int = Integer.parseInt(prop.getProperty("normal_cash_out_interval"));  // Interval of cash-out transactions for normal account
		int fraud_out_int = Integer.parseInt(prop.getProperty("fraud_cash_out_interval"));  // Interval of cash-out transactions for suspicious account
		float norm_out_min = Float.parseFloat(prop.getProperty("normal_cash_out_min"));  // Minimum amount of cash-out transactions for normal account
		float norm_out_max = Float.parseFloat(prop.getProperty("normal_cash_out_max"));  // Maximum amount of cash-out transactions for normal account
		float fraud_out_min = Float.parseFloat(prop.getProperty("fraud_cash_out_min"));  // Minimum amount of cash-out transactions for suspicious account
		float fraud_out_max = Float.parseFloat(prop.getProperty("fraud_cash_out_max"));  // Maximum amount of cash-out transactions for suspicious account
		CashOutModel.setParam(norm_out_int, fraud_out_int, norm_out_min, norm_out_max, fraud_out_min, fraud_out_max);


		// Create branches (for cash transactions)
		this.numBranches = Integer.parseInt(this.getParamters().getProperty("numBranches"));
		if(this.numBranches <= 0){
			throw new IllegalStateException("The numBranches must be positive");
		}
		for(int i=0; i<this.numBranches; i++) {
			this.branches.add(new Branch(i));
		}

		this.accountFile = this.getParamters().getProperty("accountFile");
		this.transactionFile = this.getParamters().getProperty("transactionFile");
		this.alertFile = this.getParamters().getProperty("alertFile");
		this.counterFile = this.getParamters().getProperty("counterLog");
		this.diameterFile = this.getParamters().getProperty("diameterLog");
        this.computeDiameter = Boolean.parseBoolean(this.getParamters().getProperty("computeDiameter"));

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

	private final Set<String> baseColumns = new HashSet<>(Arrays.asList("ACCOUNT_ID", "IS_FRAUD", "TX_BEHAVIOR_ID", "INIT_BALANCE", "START_DATE", "END_DATE"));

	protected void loadAccountFile(String accountFile) throws IOException{
		BufferedReader reader = new BufferedReader(new FileReader(accountFile));
		String line = reader.readLine();
		logger.info("Account CSV header: " + line);
		Map<String, Integer> columnIndex = getColumnIndices(line);
		Set<String> extraColumns = new HashSet<>(columnIndex.keySet());
		extraColumns.removeAll(baseColumns);

		while((line = reader.readLine()) != null){
			String[] elements = line.split(",");
            String accountID = elements[columnIndex.get("ACCOUNT_ID")];
			boolean isFraud = elements[columnIndex.get("IS_FRAUD")].toLowerCase().equals("true");
			int modelID = Integer.parseInt(elements[columnIndex.get("TX_BEHAVIOR_ID")]);
			float init_balance = Float.parseFloat(elements[columnIndex.get("INIT_BALANCE")]);
			int start_step = Integer.parseInt(elements[columnIndex.get("START_DATE")]);
			int end_step = Integer.parseInt(elements[columnIndex.get("END_DATE")]);

			Map<String, String> extraValues = new HashMap<>();
			for(String column : extraColumns){
			    int idx = columnIndex.get(column);
                extraValues.put(column, elements[idx]);
            }

			Account client = isFraud ? new FraudAccount(accountID, modelID, defaultInterval, init_balance, start_step, end_step, extraValues)
					: new Account(accountID, modelID, defaultInterval, init_balance, start_step, end_step, extraValues);

			int index = this.getClients().size();
			client.setBranch(this.branches.get(index % this.numBranches));
			this.getClients().add(client);
			this.idMap.put(accountID, index);
			this.schedule.scheduleRepeating(client);
		}
		int numAccounts = idMap.size();
		logger.info("Number of total accounts: " + numAccounts);
		diameter = new Diameter(numAccounts);

		reader.close();
	}

	protected void loadTransactionFile(String transactionFile) throws IOException{
		BufferedReader reader = new BufferedReader(new FileReader(transactionFile));
		String line = reader.readLine();
		Map<String, Integer> columnIndex = getColumnIndices(line);
		while((line = reader.readLine()) != null){
			String[] elements = line.split(",");
			long txID = Long.parseLong(elements[columnIndex.get("id")]);
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


	protected void loadAlertFile(String alertFile) throws IOException{
		BufferedReader reader = new BufferedReader(new FileReader(alertFile));
		String line = reader.readLine();
		Map<String, Integer> columnIndex = getColumnIndices(line);
		Map<Long, Integer> scheduleModels = new HashMap<>();
		while((line = reader.readLine()) != null){
			String[] elements = line.split(",");
			long alertID = Long.parseLong(elements[columnIndex.get("alertID")]);
//			long clientID = Long.parseLong(elements[columnIndex.get("clientID")]);
            String clientID = elements[columnIndex.get("clientID")];

			boolean isSubject = elements[columnIndex.get("isSubject")].toLowerCase().equals("true");
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

			Alert fg;
			if(alertGroups.containsKey(alertID)){
				fg = alertGroups.get(alertID);
			}else{
				FraudTransactionModel model = FraudTransactionModel.getModel(modelID, minAmount, maxAmount, minStep, maxStep);
				fg = new Alert(alertID, model, this);
				alertGroups.put(alertID, fg);
			}
			Account c = getClientFromID(clientID);
			fg.addMember(c);
			if(isSubject){
				fg.setSubjectAccount((FraudAccount) c);
				c.setCase(true);
			}
			scheduleModels.put(alertID, scheduleID);
		}
		for(long alertID : scheduleModels.keySet()){
			int modelID = scheduleModels.get(alertID);
			alertGroups.get(alertID).getModel().setSchedule(modelID);
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

		String dirPath = System.getProperty("user.dir")  +"//outputs//" + AMLSim.simulatorName;
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

		// TODO: Load actions (transaction types) from configuration files
        this.actions.add("TRANSFER");
//		this.actions.add("CASH_IN");
//		this.actions.add("CASH_OUT");
//		this.actions.add("DEBIT");
//		this.actions.add("DEPOSIT");
//		this.actions.add("PAYMENT");
//		this.actions.add("TRANSFER");
	}


	private void initBufWriter(String logFileName) {
		try {
			FileWriter writer = new FileWriter(new File(logFileName));
			this.bufWriter = new BufferedWriter(writer);
			this.bufWriter.write("step,type,amount,nameOrig,oldbalanceOrg,newbalanceOrig,nameDest,oldbalanceDest,newbalanceDest,isFraud,alertID\n");
			this.bufWriter.close();
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
	
	public void executeSimulation(){
		//Load the parameters from the .property file
		loadParametersFromFile();

		// increase transfer limit with the current loop
		initSimulatorName();
		loadAggregatedFile();

		//Initiate the dumpfile output writer
		txLogFileName = System.getProperty("user.dir")  +"//outputs//" + AMLSim.simulatorName + "//" + AMLSim.simulatorName + "_log.csv";
		initBufWriter(txLogFileName);

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

	private double getDoublePrecision(double d) {
		final int precision = 2;
		return (new BigDecimal(d)).setScale(precision, BigDecimal.ROUND_HALF_UP).doubleValue();
	}

	public static void handleTransaction(long step, String desc, float amt, Account orig, Account dest, boolean fraud, long aid){
//		long origID = orig.getID();
        String origID = orig.getID();

		float origBefore = (float)orig.getBalance();
		orig.withdraw(amt);
		float origAfter = (float)orig.getBalance();

//		long destID = dest.getID();
        String destID = dest.getID();

		float destBefore = (float)dest.getBalance();
		dest.deposit(amt);
		float destAfter = (float)dest.getBalance();

		txs.addTransaction(step, desc, amt, origID, destID, origBefore, origAfter, destBefore, destAfter, fraud, aid);
		diameter.addEdge(origID, destID);
	}

	public void writeDiameter(long step, double[] result){
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
		if(args.length < 6){
			System.err.println("Usage: java amlsim.AMLSim -file [PropertyFile] -for [Steps] -r [Repeats] [-name [SimulatorName]]");
			System.exit(1);
		}

		int nrOfTimesRepeat = Integer.parseInt(args[5]);
		
		for(int i=0; i<nrOfTimesRepeat; i++){
			AMLSim p = new AMLSim(1);
			p.setCurrentLoop(i);
			p.runSimulation(args);
		}
	}
}

