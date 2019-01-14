package amlsim.obsolete;

import amlsim.AMLSim;

import java.util.Random;

/**
 * @deprecated This class is obsolete
 */
public class StepCalculator {

    private static Random random = new Random();


    public static long getStepTo(long end){
        return getStepRange(0, end);
    }

    public static long getStepFrom(long start){
        long end = AMLSim.getNumOfSteps();
        return getStepRange(start, end);
    }

    public static long getStepRange(long start, long end){
        if(start == end){
            return start;
        }
        long range = (end - start);
        return random.nextInt() % range + start;
    }
}

