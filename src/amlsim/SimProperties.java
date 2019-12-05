package amlsim;

import java.io.*;
import java.nio.file.*;
import org.json.*;


/**
 * Simulation properties and global parameters loaded from the configuration JSON file
 */
public class SimProperties {

    private static final String separator = File.separator;
    private JSONObject generalProp;
    private JSONObject simProp;
    private JSONObject inputProp;
    private JSONObject outputProp;
    private JSONObject cashInProp;
    private JSONObject cashOutProp;
    private String workDir;
    private float marginRatio;
    private int seed;
    private String simName;

    private int normalTxInterval;
//    private int sarTxInterval;
    private float minTxAmount;  // Minimum base (normal) transaction amount
    private float maxTxAmount;  // Maximum base (suspicious) transaction amount

    SimProperties(String jsonName) throws IOException{
        String jsonStr = loadTextFile(jsonName);
        JSONObject jsonObject = new JSONObject(jsonStr);
        JSONObject defaultProp = jsonObject.getJSONObject("default");

        generalProp = jsonObject.getJSONObject("general");
        simProp = jsonObject.getJSONObject("simulator");
        inputProp = jsonObject.getJSONObject("temporal");  // Input directory of this simulator is temporal directory
        outputProp = jsonObject.getJSONObject("output");

        normalTxInterval = simProp.getInt("transaction_interval");
//        sarTxInterval = simProp.getInt("sar_interval");
        minTxAmount = defaultProp.getFloat("min_amount");
        maxTxAmount = defaultProp.getFloat("max_amount");

        System.out.printf("General transaction interval: %d\n", normalTxInterval);
//        System.out.printf("Transaction interval: Normal = %d, Suspicious = %d\n", normalTxInterval, sarTxInterval);
        System.out.printf("Base transaction amount: Normal = %f, Suspicious= %f\n", minTxAmount, maxTxAmount);
        
        cashInProp = defaultProp.getJSONObject("cash_in");
        cashOutProp = defaultProp.getJSONObject("cash_out");
        marginRatio = defaultProp.getFloat("margin_ratio");

        String envSeed = System.getenv("RANDOM_SEED");
        seed = envSeed != null ? Integer.parseInt(envSeed) : generalProp.getInt("random_seed");
        System.out.println("Random seed: " + seed);

        simName = System.getenv("SIMULATION_NAME");
        if(simName == null){
            simName = generalProp.getString("simulation_name");
        }
        System.out.println("Simulation name: " + simName);

        String simName = getSimName();  // generalProp.getString("simulation_name");
        workDir = inputProp.getString("directory") + separator + simName + separator;
        System.out.println("Working directory: " + workDir);
    }

    private static String loadTextFile(String jsonName) throws IOException{
        Path file = Paths.get(jsonName);
        byte[] bytes = Files.readAllBytes(file);
        return new String(bytes);
    }

    String getSimName(){
        return simName;
    }

    int getSeed(){
        return seed;
    }

    public int getSteps(){
        return generalProp.getInt("total_steps");
    }

    boolean isComputeDiameter(){
        return simProp.getBoolean("compute_diameter");
    }

    int getTransactionLimit(){
        return simProp.getInt("transaction_limit");
    }

    int getNormalTransactionInterval(){
        return normalTxInterval;
    }

    public float getNormalBaseTxAmount(){
        return minTxAmount;
    }

    public float getSuspiciousTxAmount(){
        return maxTxAmount;
    }

//    int getSarTransactionInterval(){
//        return sarTxInterval;
//    }

//    float getSatBalanceRatio(){
//        return simProp.getFloat("sar_balance_ratio");
//    }

    public float getMarginRatio(){
        return marginRatio;
    }

    int getNumBranches(){
        return simProp.getInt("numBranches");
    }

    String getInputAcctFile(){
        return workDir + inputProp.getString("accounts");
    }

    String getInputTxFile(){
        return workDir + inputProp.getString("transactions");
    }

    String getInputAlertMemberFile(){
        return workDir + inputProp.getString("alert_members");
    }

    String getOutputTxLogFile(){
        return workDir + outputProp.getString("transaction_log");
    }

    public String getOutputAlertMemberFile(){
        return workDir + outputProp.getString("alert_members");
    }

    public String getOutputAlertTxFile(){
        return workDir + outputProp.getString("alert_transactions");
    }

    String getOutputDir(){
        return workDir;
    }

    String getCounterLogFile(){
        return workDir + outputProp.getString("counter_log");
    }

    String getDiameterLogFile(){
        return workDir + outputProp.getString("diameter_log");
    }

    int getCashTxInterval(boolean isCashIn, boolean isSAR){
        String key = isSAR ? "fraud_interval" : "normal_interval";
        return isCashIn ? cashInProp.getInt(key) : cashOutProp.getInt(key);
    }

    float getCashTxMinAmount(boolean isCashIn, boolean isSAR){
        String key = isSAR ? "fraud_min_amount" : "normal_min_amount";
        return isCashIn ? cashInProp.getFloat(key) : cashOutProp.getFloat(key);
    }

    float getCashTxMaxAmount(boolean isCashIn, boolean isSAR){
        String key = isSAR ? "fraud_max_amount" : "normal_max_amount";
        return isCashIn ? cashInProp.getFloat(key) : cashOutProp.getFloat(key);
    }
}


