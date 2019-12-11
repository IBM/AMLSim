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

    private static float SAR2SAR_EDGE_PROB = 1.0F;
    private static float SAR2NORMAL_EDGE_PROB = 0.5F;

    private static float SAR2SAR_AMOUNT_RATIO = 2.0F;
    private static float SAR2NORMAL_AMOUNT_RATIO = 1.0F;
    private static float NORMAL2SAR_AMOUNT_RATIO = 0.5F;
    private static float NORMAL2NORMAL_AMOUNT_RATIO = 1.0F;

    /**
     * Whether no adjustment parameters in this class will be applied for transactions
     * @return If true, all normal transactions are not affected by any adjustment parameters
     */
    public static boolean isUnused(){
//        return prop == null;
        return false;
    }

    private static float getRatio(String key){
        return Float.parseFloat(prop.getProperty(key, "1.0"));
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

        SAR2SAR_EDGE_PROB = getRatio("sar2sar.edge.prob");
        SAR2NORMAL_EDGE_PROB = getRatio("sar2normal.edge.prob");

        SAR2SAR_AMOUNT_RATIO = getRatio("sar2sar.amount.ratio");
        SAR2NORMAL_AMOUNT_RATIO = getRatio("sar2normal.amount.ratio");
        NORMAL2SAR_AMOUNT_RATIO = getRatio("normal2sar.amount.ratio");
        NORMAL2NORMAL_AMOUNT_RATIO = getRatio("normal2normal.amount.ratio");

        return prop;
    }

    /**
     * Generate an up to 10% ratio noise for the base transaction amount
     * @return Amount ratio [0.9, 1.1]
     */
    public static float generateAmountRatio(){  // [0.9, 1.1]
        return rand.nextFloat() * 0.2F + 0.9F;
    }

    /**
     * Adjust transaction amount from the given accounts and the base amount
     * @param orig Originator account
     * @param bene Beneficiary account
     * @param baseAmount Base amount
     * @return Adjusted amount (If it should not make this transaction, return non-positive value)
     */
    public static float adjustAmount(Account orig, Account bene, float baseAmount){
        // Generate decentralized amount with up to 10% noise
        float amount = baseAmount * generateAmountRatio();

        if(isUnused()){
            return amount;
        }
        // TODO: Make the following parameters customizable from command lines as Java system properties
        float ratio;
        if(orig.isSAR()){  // SAR originator
            if(bene.isSAR()){  // SAR -> SAR
                ratio = SAR2SAR_AMOUNT_RATIO;
            }else{  // SAR -> Normal
                ratio = SAR2NORMAL_AMOUNT_RATIO;
            }
        }else{  // Normal originator
            if(bene.isSAR()){  // Normal -> SAR
                ratio = NORMAL2SAR_AMOUNT_RATIO;
            }else{  // Normal -> Normal
                ratio = NORMAL2NORMAL_AMOUNT_RATIO;
            }
//            int actionID = rand.nextInt(100);
//            if(actionID < 5){  // High-amount payment transaction (near to the upper limit) with 5% of the time
//                ratio = 30;
//            }else if(actionID < 50){  // Half-amount transaction with 45% of the time
//                ratio = 0.5F;
//            }else{
//                ratio = 0;  // Skip transaction with 50% of the time
//            }
        }
        return amount * ratio;
    }

    /**
     * Determine whether the transaction edge should be actually added between the given accounts
     * @param orig Originator account
     * @param bene Beneficiary account
     * @return If the transaction should be actually added, return true.
     */
    public static boolean shouldAddEdge(Account orig, Account bene){
        if(isUnused()){  // Add this edge without qualification
            return true;
        }
        // TODO: Make the following parameters customizable from command lines as Java system properties
        float benePropThreshold = 0.1F;  // Proportion of SAR beneficiary accounts of the originator account
        int beneNumThreshold = (int) Math.floor(1 / benePropThreshold);

        int numNeighbors = orig.getBeneList().size();
        float propSARBene = orig.getPropSARBene();

        if(orig.isSAR()){  // SAR originator
            if(bene.isSAR()){  // SAR -> SAR
                return true;
            }else{  // SAR -> Normal
                // Allow edge creations if the ratio of SAR beneficiary accounts is enough large
                return propSARBene > benePropThreshold;
            }
        }else{  // Normal originator
            if(bene.isSAR()){  // Normal -> SAR
                // Create a transaction edge if the ratio of SAR beneficiary accounts is still large
                boolean flag = numNeighbors > beneNumThreshold; // && propSARBene >= benePropThreshold;
//                if(flag) {
//                    System.out.print(orig.getID() + " -> " + bene.getID() + " ");
//                    orig.printBeneList();
//                    System.out.flush();
//                }
                return flag;
            }else{  // Normal -> Normal
                return true;
            }
        }
    }

}
