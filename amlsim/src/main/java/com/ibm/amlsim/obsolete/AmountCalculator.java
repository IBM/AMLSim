package com.ibm.amlsim.obsolete;

import com.ibm.amlsim.Account;

import java.io.*;
import java.util.Properties;
import java.util.Random;
import static java.lang.Math.cbrt;

/**
 * @deprecated This class is obsolete
 */
public class AmountCalculator {

    private static Properties prop = new Properties();
    private static Random random = new Random();

    private static float trustedAvg = 0;
    private static float trustedDiv = 0;
    private static float untrustedAvg = 0;
    private static float untrustedDiv = 0;

    public static void load(String fname){
        try {
            InputStreamReader reader = new InputStreamReader(new FileInputStream(fname));
            prop.load(reader);
        } catch (IOException e) {
            e.printStackTrace();
        }
        trustedAvg = Float.parseFloat(prop.getProperty("trusted.avg"));
        trustedDiv = Float.parseFloat(prop.getProperty("trusted.div"));
        untrustedAvg = Float.parseFloat(prop.getProperty("untrusted.avg"));
        untrustedDiv = Float.parseFloat(prop.getProperty("untrusted.div"));
    }

    public static double getAmount(boolean isTrusted, String country, String businessType){

        double trustedAmount = isTrusted ? random.nextGaussian() * trustedDiv + trustedAvg
                : random.nextGaussian() * untrustedDiv + untrustedAvg;

        float countryAvg = Float.parseFloat(prop.getProperty(country + ".avg"));
        float countrydiv = Float.parseFloat(prop.getProperty(country + ".div"));
        double countryAmount = random.nextGaussian() * countrydiv + countryAvg;

        float businessAvg = Float.parseFloat(prop.getProperty(businessType + ".avg"));
        float businessDiv = Float.parseFloat(prop.getProperty(businessType + ".div"));
        double businessAmount = random.nextGaussian() * businessAvg + businessDiv;

        return cbrt(trustedAmount * countryAmount * businessAmount);
    }

    public static double getAmount(Account client){
        double balance = client.getBalance();

        return balance;
    }

}

