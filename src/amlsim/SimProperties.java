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

    SimProperties(String jsonName) throws IOException{
        String jsonStr = loadTextFile(jsonName);
        JSONObject jsonObject = new JSONObject(jsonStr);
        generalProp = jsonObject.getJSONObject("general");
        simProp = jsonObject.getJSONObject("simulator");
        inputProp = jsonObject.getJSONObject("temporal");  // Input directory of this simulator is temporal directory
        outputProp = jsonObject.getJSONObject("output");
        cashInProp = jsonObject.getJSONObject("default").getJSONObject("cash_in");
        cashOutProp = jsonObject.getJSONObject("default").getJSONObject("cash_out");
        marginRatio = jsonObject.getJSONObject("default").getFloat("margin_ratio");

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
        return generalProp.getString("simulation_name");
    }

    int getSeed(){
        return generalProp.getInt("random_seed");
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

    int getTransactionInterval(){
        return simProp.getInt("transaction_interval");
    }

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


