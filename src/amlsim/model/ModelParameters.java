package amlsim.model;

import java.io.*;
import java.util.Random;
import java.util.Properties;

import amlsim.AMLSim;
import amlsim.Account;

/**
 * Adjust transaction parameters for fine-tuning of the transaction network
 */
public class ModelParameters {

    private static Random rand = new Random(AMLSim.getSeed());
    private static Properties prop = loadProperties();

    public static boolean isDisabled(){
//        return prop == null;
        return false;
    }

    private static Properties loadProperties(){
        String key = "MODEL_PARAM";
        String propFile = System.getenv(key);
        if(propFile == null){
//            System.err.println("Model parameter file is not specified: " + key);
            return null;
        }
        System.out.println("Model parameter file: " + propFile);
        try{
            prop = new Properties();
            prop.load(new FileInputStream(propFile));
        }catch (IOException e){
            System.err.println("Cannot load model parameter file: " + propFile);
            e.printStackTrace();
            return null;
        }
        return prop;
    }

    /**
     * Generate the adjustment ratio of the transaction amount
     * @return Amount ratio [0.9, 1.1]
     */
    public static float generateAmountRatio(){  // [0.9, 1.1]
        return rand.nextFloat() * 0.2F + 0.9F;
    }

    public static float computeAmount(Account orig, Account bene, float baseAmount){
        float amount = baseAmount * generateAmountRatio();

        if(isDisabled()){
            return amount;
        }
        // TODO: Make the following parameters customizable from command lines as Java system properties
        float ratio = 1.0F;
        if(orig.isSAR()){  // SAR originator
            if(bene.isSAR()){  // SAR -> SAR
                ratio = 2.0F;
            }else{  // SAR -> Normal
//                ratio = 1.0F;
            }
        }else{  // Normal originator
            int actionID = rand.nextInt(100);
            if(actionID < 5){  // High-amount payment transaction (near to the upper limit) with 5% of the time
                ratio = 30;
            }else if(actionID < 50){  // Half-amount transaction with 45% of the time
                ratio = 0.5F;
            }else{
                ratio = 0;  // Skip transaction with 50% of the time
            }
        }
        return amount * ratio;
    }

    public static boolean shouldAddEdge(Account orig, Account bene){
        if(isDisabled()){
            return true;
        }
        // TODO: Make the following parameters customizable from command lines as Java system properties
        float benePropThreshold = 0.01F;  // Proportion of SAR beneficiary accounts of the originator account
        int beneNumThreshold = 10;  // Number of total neighbor beneficiary accounts of the originator account

        int numNeighbors = orig.getBeneList().size();
        if(orig.isSAR()){  // SAR originator
            if(bene.isSAR()){  // SAR -> SAR
                return true;
            }else{  // SAR -> Normal
//                return numNeighbors < beneNumThreshold;
                return orig.getPropSARBene() <= benePropThreshold;
            }
        }else{  // Normal originator
            if(bene.isSAR()){  // Normal -> SAR
                return numNeighbors > beneNumThreshold && orig.getPropSARBene() < benePropThreshold;
            }else{  // Normal -> Normal
                return true;
            }
        }
    }

}
